#!/usr/bin/python

from DB import DB
from Httpy import Httpy
from ImageUtils import ImageUtils

from os        import path, remove
from shutil    import copy2
from time      import sleep, gmtime
from calendar  import timegm
from threading import Thread
from traceback import format_exc

MAX_THREADS = 10

class RipManager(object):

	def __init__(self):
		self.db = DB()
		self.httpy = Httpy()
		self.current_threads = []
		self.results = []
		self.to_remove = []

	def start(self):
		stale_count = self.db.count('urls', 'pending != 0')
		if stale_count > 0:
			print 'MAIN: found %d stale (interrupted) URLs, marking as non-pending...' % stale_count
			self.db.update('urls', 'pending = 0')
			self.db.commit()
		print 'MAIN: starting infinite loop...'
		already_printed_sleep_msg = False
		while True:
			sleep(0.1)
			while len(self.results) > 0:
				# self.results is the list of downloaded medias to be added to the DB
				result = self.results.pop()
				self.handle_result(result)

			# Remove recently-completed rips
			while len(self.to_remove) > 0:
				(albumid, iindex) = self.to_remove.pop()
				self.db.delete('urls', 'album_id = ? and i_index = ?', [ albumid, iindex ] )
			self.db.commit()

			try:
				# Get next URL to retrieve
				url = self.get_next_url()
			except Exception, e:
				if str(e) == 'no URLs found':
					if not already_printed_sleep_msg:
						already_printed_sleep_msg = True
						print 'MAIN: no urls to get, sleeping 500ms'
					sleep(0.5)
				else:
					print 'MAIN: get_next_url(): Exception: %s:\n%s' % (str(e), format_exc())
				continue

			# We have a URL to download & add to DB (url)
			already_printed_sleep_msg = False
			# Wait for thread count to drop
			while len(self.current_threads) >= MAX_THREADS:
				sleep(0.1)
			self.current_threads.append(None)
			# Create new thread to download the media, add to self.results
			print 'MAIN: %s #%d: launching handler for: %s' % (url['path'], url['i_index'], url['url'])

			# Create subdirs from main thread to avoid race condition
			dirname = path.join(ImageUtils.get_root(), 'rips', url['path'], 'thumbs')
			ImageUtils.create_subdirectories(dirname)

			args = (url,)
			t = Thread(target=self.retrieve_result_from_url, args=args)
			t.start()
			# Thread will pop one out of self.current_threads when completed

	def handle_result(self, result):
		# Insert result into DB
		values = (
			result['album_id'],
			result['i_index'],
			result['url'],
			result['valid'],
			result['error'],
			result['type'],
			result['image_name'],
			result['width'],
			result['height'],
			result['filesize'],
			result['thumb_name'],
			result['t_width'],
			result['t_height'],
			result['metadata']
		)
		self.db.insert('medias', values)
		# Delete from URLs
		self.db.delete('urls', 'album_id = ? and i_index = ?', [ result['album_id'], result['i_index'] ] )
		self.db.commit()

		# Check if this was the last media to add to DB
		album_id = result['album_id']
		medias_count = self.db.count('medias', 'album_id = ?', [album_id])
		album_count = self.db.select_one('count', 'albums', 'rowid = ?', [album_id])
		if medias_count == album_count:
			# No more URLs to retrieve, finish up
			print 'MAIN: %s: completed (total: %d)' % (result['path'], medias_count)
			filesize = self.db.select_one('sum(filesize)', 'medias', 'album_id = ?', [album_id])
			now = timegm(gmtime())
			count = self.db.count('medias', 'album_id = ?', [album_id])
			self.db.update('albums', 'ready = 1, pending = 0, filesize = ?, modified = ?, accessed = ?, count = ?', 'rowid = ?', [filesize, now, now, count, album_id])
			self.db.commit()

	def get_next_url(self):
		# Return next URL to retrieve, removes from DB
		if self.db.count('urls', 'pending = 0') == 0:
			raise Exception('no URLs found')
		q = '''
			select
				album_id, urls.i_index, urls.url, urls.saveas, urls.type, urls.metadata, urls.added, albums.path
			from urls inner join albums on urls.album_id = albums.rowid
			where urls.pending = 0
			order by added asc, i_index asc
			limit 1
		'''
		cursor = self.db.conn.cursor()
		curexec = cursor.execute(q)
		url = {}
		curexec = cursor.fetchall()
		for (album_id, index, url, saveas, mediatype, metadata, added, albumpath) in curexec:
			url = {
				'album_id' : album_id,
				'i_index'  : index,
				'url'      : url,
				'path'     : albumpath,
				'saveas'   : saveas,
				'type'     : mediatype,
				'metadata' : metadata,
				'added'    : added,
			}
			break # We only wanted the first URL (limit is 1 anyway)
		cursor.close()
		if url == {}:
			raise Exception('no URLs found on join')

		# Mark URL as 'pending'
		self.db.update('urls', 'pending = 1', 'album_id = ? and i_index = ?', [ url['album_id'], url['i_index'] ] )
		self.db.commit()
		return url

	def retrieve_result_from_url(self, url):
		# url contains album_id, index, url, type, path, and saveas

		# TODO logging into dirname/log.txt

		# Construct base result
		result = {
			'album_id'  : url['album_id'],
			'i_index'   : url['i_index'],
			'url'       : url['url'],
			'valid'     : 0,    #
			'error'     : None, #
			'type'      : url['type'],
			'image_name': url['saveas'],
			'filesize'  : 0,    #
			'width'     : 0,    #
			'height'    : 0,    #
			'thumb_name': None, #
			't_width'   : 0,    #
			't_height'  : 0,    #
			'metadata'  : url['metadata'],
			'path'      : url['path']
		}

		# Get save directory
		dirname = path.join(ImageUtils.get_root(), 'rips', url['path'])

		# Generate save path
		saveas = path.join(dirname, url['saveas'])
		if path.exists(saveas):
			print 'THREAD: %s: removing existing file %s' % (url['path'], saveas)
			remove(saveas)

		try:
			meta = self.httpy.get_meta(url['url'])
		except Exception, e:
			# Can't get meta? Can't get image!
			print 'THREAD: %s: failed to get_meta from %s: %s\n%s' % (url['path'], url['url'], str(e), format_exc())
			result['error'] = 'failed to get metadata from %s: %s\n%s' % (url['url'], str(e), format_exc())
			self.to_remove.append( (url['album_id'], url['i_index'] ) )
			self.results.append(result)
			self.current_threads.pop()
			return

		if 'imgur.com' in url['url'] and 'Content-length' in meta and meta['Content-length'] == '503':
			print 'THREAD: %s: imgur image was not found (503b) at %s' % (url['path'], url['url'])
			result['error'] = 'imgur image was not found (503b) at %s' % url['url']
			self.to_remove.append( (url['album_id'], url['i_index'] ) )
			self.results.append(result)
			self.current_threads.pop()
			return

		if 'Content-type' in meta and 'html' in meta['Content-Type'].lower():
			print 'THREAD: %s: url returned HTML content-type at %s' % (url['path'], url['url'])
			result['error'] = 'url returned HTML content-type at %s' % url['url']
			self.to_remove.append( (url['album_id'], url['i_index'] ) )
			self.results.append(result)
			self.current_threads.pop()
			return

		if meta['content-type'].lower().endswith('png'):
			# image/png
			result['type'] = 'image'
			if not saveas.lower().endswith('png'):
				saveas = saveas[:saveas.rfind('.')+1] + 'png'
		elif meta['content-type'].lower().endswith('jpeg') or meta['content-type'].lower().endswith('jpg'):
			# image/jpg
			result['type'] = 'image'
			if not saveas.lower().endswith('jpg'):
				saveas = saveas[:saveas.rfind('.')+1] + 'jpg'
		elif meta['content-type'].lower().endswith('gif'):
			# image/gif
			result['type'] = 'image'
			if not saveas.lower().endswith('gif'):
				saveas = saveas[:saveas.rfind('.')+1] + 'gif'
		elif meta['content-type'].lower().endswith('mp4'):
			# video/mp4
			result['type'] = 'video'
			if not saveas.lower().endswith('mp4'):
				saveas = saveas[:saveas.rfind('.')+1] + 'mp4'
		elif meta['content-type'].lower().endswith('flv'):
			# video/flv
			result['type'] = 'video'
			if not saveas.lower().endswith('flv'):
				saveas = saveas[:saveas.rfind('.')+1] + 'flv'
		elif meta['content-type'].lower().endswith('wmv'):
			# video/wmv
			result['type'] = 'video'
			if not saveas.lower().endswith('wmv'):
				saveas = saveas[:saveas.rfind('.')+1] + 'wmv'

		result['image_name'] = path.basename(saveas)
		# Attempt to dowload image at URL
		try:
			self.httpy.download(url['url'], saveas)
		except Exception, e:
			print 'THREAD: %s: failed to download %s to %s: %s\n%s' % (url['path'], url['url'], saveas, str(e), str(format_exc()))
			result['error'] = 'failed to download %s to %s: %s\n%s' % (url['url'], saveas, str(e), str(format_exc()))
			self.to_remove.append( (url['album_id'], url['i_index'] ) )
			self.results.append(result)
			self.current_threads.pop()
			return

		# Save image info
		result['filesize'] = path.getsize(saveas)
		try:
			(result['width'], result['height']) = ImageUtils.get_dimensions(saveas)
		except Exception, e:
			# This fails if we can't identify the image file. Consider it errored
			print 'THREAD: %s: failed to identify image file %s from %s: %s\n%s' % (url['path'], saveas, url['url'], str(e), format_exc())
			result['error'] = 'failed to identify image file %s from %s: %s\n%s' % (saveas, url['url'], str(e), format_exc())
			self.to_remove.append( (url['album_id'], url['i_index'] ) )
			self.results.append(result)
			self.current_threads.pop()
			return

		# Get thumbnail
		tsaveas = path.join(dirname, 'thumbs', url['saveas'])
		try:
			(tsaveas, result['t_width'], result['t_height']) = ImageUtils.create_thumbnail(saveas, tsaveas)
		except Exception, e:
			# Failed to create thumbnail, use default
			print 'THREAD: %s: failed to create thumbnail: %s' % (url['path'], str(e))
			tsaveas = '/'.join(['ui', 'images', 'nothumb.png'])
			result['t_width'] = result['t_height'] = 160
		result['thumb_name'] = path.basename(tsaveas)

		result['valid'] = 1
		# Delete from URLs list
		self.results.append(result)
		self.current_threads.pop()

	@staticmethod
	def exit_if_already_started():
		from commands import getstatusoutput
		from sys import exit
		(status, output) = getstatusoutput('ps aux')
		running_processes = 0
		for line in output.split('\n'):
			if 'python' in line and 'RipManager.py' in line and not '/bin/sh -c' in line:
				running_processes += 1
		if running_processes > 1:
			exit(0) # Quit silently if this script is already running

if __name__ == '__main__':
	RipManager.exit_if_already_started()
	rm = RipManager()
	rm.start()
