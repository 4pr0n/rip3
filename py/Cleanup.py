#!/usr/bin/python

from DB import DB
from os import path as ospath
from shutil import rmtree
from time import gmtime
from calendar import timegm
from ImageUtils import ImageUtils


class Cleanup(object):
	MAX_TOTAL_BYTES   = 150 * 1024 * 1024 * 1024
	MAX_EMPTY_SECONDS = 3600 * 2
	MAX_REPORTS       = 3
	IGNORE_ALBUMS = [
		'imgur_reactiongifsarchive',
		'imgur_inphinitechaos',
		'imgur_jwinston',
		'flickr_herosjourneymythology45surf',
		'flickr_herosjourneymythology45surf_72157631380242956',
		'imgur_markedone911',
		'imgur_jAjVu',
		'imgur_iateacrayon',
		'imgur_wIAaa',
		'imgur_imouto'
	]


	def __init__(self):
		self.db = DB()
	

	def cleanup_empty_albums(self):
		'''
			Deletes albums more than MAX_EMPTY_SECONDS old with no images.
		'''
		now = timegm(gmtime())
		q = '''
			select rowid, path
			from albums
			where created > %d and count == 0
			order by created desc
		''' % (now - Cleanup.MAX_EMPTY_SECONDS)
		cursor = self.db.conn.cursor()
		for (rowid, path,) in cursor.execute(q):
			if self.path_in_ignore(path):
				continue
			self.delete_album(cursor, rowid, path)
		self.db.commit()
		cursor.close()


	def cleanup_reported_albums(self):
		'''
			Deletes albums with more than MAX_REPORTS
		'''
		now = timegm(gmtime())
		q = '''
			select rowid, path
			from albums
			where reports >= %d
			order by created desc
		''' % Cleanup.MAX_REPORTS
		cursor = self.db.conn.cursor()
		for (rowid, path,) in cursor.execute(q):
			if self.path_in_ignore(path):
				continue
			self.delete_album(cursor, rowid, path)
		self.db.commit()
		cursor.close()


	def cleanup_stale_albums(self):
		'''
			Ensures files don't exceed MAX_TOTAL_BYTES, 
			deletes least-frequently accessed albums first.
		'''
		q = '''
			select rowid, path, filesize
			from albums
			order by accessed desc
		'''
		total_size = 0
		cursor = self.db.conn.cursor()
		for (rowid, path, filesize,) in cursor.execute(q):
			if self.path_in_ignore(path):
				continue
			total_size += filesize
			if total_size > Cleanup.MAX_TOTAL_BYTES:
				self.delete_album(cursor, rowid, path)
		self.db.commit()
		cursor.close()


	def delete_album(self, cursor, rowid, path):
		# Delete images
		cursor.execute('delete from medias where album_id = ?', [rowid])
		# Delete pending URLs
		cursor.execute('delete from urls where album_id = ?', [rowid])
		# Delete album
		cursor.execute('delete from albums where path = ?', [path])
		# Delete directory + files
		path = ospath.join(ImageUtils.get_root(), path)
		rmtree(path)


	def path_in_ignore(self, path):
		'''
			Checks if path is in the IGNORE_ALBUMS list
		'''
		for ig in Cleanup.IGNORE_ALBUMS:
			if path.endswith(ig):
				return True
		return False


if __name__ == '__main__':
	c = Cleanup()
	c.cleanup_empty_albums()
	c.cleanup_reported_albums()
	c.cleanup_stale_albums()
