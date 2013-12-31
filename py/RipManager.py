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

MAX_THREADS = 3

class RipManager(object):

	def __init__(self):
		self.db = DB()
		self.httpy = Httpy()
		self.results = [None] * MAX_THREADS

	def start(self):
		while True:
			sleep(0.1)
			if len(self.results) > 0:
				result = self.results.pop()
				# Parse result
				if result != None:
					self.handle_result(result)
				# Get next URL to retrieve
				try:
					url = self.get_next_url()
				except Exception, e:
					self.results.append(None)
					if str(e) == 'no URLs found':
						print 'no urls to get, sleeping 500ms'
						sleep(0.5)
					else:
						print str(e), format_exc()
					continue
				# Create new thread
				args = (url,)
				print 'handling: %s' % str(url)
				t = Thread(target=self.retrieve_result_from_url, args=args)
				t.start()
			else:
				print 'empty, sleeping 500ms'
				sleep(0.5)

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
		if self.db.count('urls', 'album_id = ?', [result['album_id']]) == 0:
			# No more URLs to retrieve
			album_id = result['album_id']
			filesize = self.db.select_one('sum(filesize)', 'medias', 'album_id = ?', [album_id])
			count = self.db.count('medias', 'album_id = ?', [album_id])
			now = timegm(gmtime())
			self.db.update('albums', 'ready = 1, pending = 0, filesize = ?, modified = ?, accessed = ?, count = ?', 'rowid = ?', [filesize, now, now, count, album_id])
		self.db.commit()

	def get_next_url(self):
		# Return next URL to retrieve, removes from DB
		if self.db.count('urls') == 0:
			raise Exception('no URLs found')
		q = '''
			select
				album_id, urls.i_index, urls.url, urls.saveas, urls.type, urls.metadata, urls.added, albums.path
			from urls inner join albums on urls.album_id = albums.rowid
			order by added desc, i_index asc
			limit 1
		'''
		cursor = self.db.conn.cursor()
		curexec = cursor.execute(q)
		url = {}
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
			break
		if url == {}:
			raise Exception('no URLs found on join')
		q = 'delete from urls where album_id = ? and i_index = ?'
		cursor.execute( q, [ url['album_id'], url['i_index'] ] )
		cursor.close()
		self.db.commit()
		return url

	def retrieve_result_from_url(self, url):
		# URL contains album_id, index, url, type, path, and saveas

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
			'width'     : 0,    #
			'height'    : 0,    #
			'thumb_name': None, #
			't_width'   : 0,    #
			't_height'  : 0,    #
			'metadata'  : url['metadata']
		}

		# Create save dir as needed
		dirname = path.join(ImageUtils.get_root(), 'rips', url['path'])
		ImageUtils.create_subdirectories(dirname)

		# Generate save path
		saveas = path.join(dirname, url['saveas'])
		if path.exists(saveas):
			remove(saveas)

		# TODO get metadata on image, enforce type.
		# if (404) or (imgur and size=503), don't bother downloading

		# Attempt to dowload image at URL
		try:
			self.httpy.download(url['url'], saveas)
		except Exception, e:
			result['error'] = 'failed to download %s to %s: %s\n%s' % (url['url'], saveas, str(e), str(format_exc()))
			self.results.append(result)
			return

		# Save image info
		result['filesize'] = path.getsize(saveas)
		(result['width'], result['height']) = ImageUtils.get_dimensions(saveas)

		# Get thumbnail
		ImageUtils.create_subdirectories(path.join(dirname, 'thumbs'))
		tsaveas = path.join(dirname, 'thumbs', url['saveas'])
		try:
			(tsaveas, result['t_width'], result['t_height']) = ImageUtils.create_thumbnail(saveas, tsaveas)
		except Exception, e:
			# Failed to create thumbnail, use default
			tsaveas = path.join(ImageUtils.get_root(), 'ui', 'images', 'nothumb.png')
			result['t_width'] = result['t_height'] = 160
		result['thumb_name'] = path.basename(tsaveas)

		result['valid'] = 1
		self.results.append(result)
	
if __name__ == '__main__':
	rm = RipManager()
	rm.start()
