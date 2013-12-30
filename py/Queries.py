#!/usr/bin/python

from DB import DB

class Queries(object):

	@staticmethod
	def get_rips_by_user(user):
		db = DB()
		q = '''
			select
				name, url, host, ready, filesize, path, created, accessed, count, views
			from albums
			where author like ?
		'''
		cursor = db.conn.cursor()
		curexec = cursor.execute(q, [user])
		results = []
		for (name, url, host, ready, filesize, path, created, accessed, count, views) in curexec:
			results.append({
				'host' : host,
				'name' : name,
				'url'  : url,
				'ready' : ready,
				'size' : filesize,
				'path' : path,
				'created' : created,
				'accessed' : accessed,
				'count' : count,
				'views' : views
			})

		return {
			'results' : results
		}
