#!/usr/bin/python

def delete_album(host, album, blacklist, reason, admin):
	from shutil import rmtree
	from os import path as ospath
	from DB import DB

	db = DB()
	if db.count('albums', 'host = ? and name = ?', [host, album]) == 0:
		raise Exception('album %s does not exist' % album)

	response = ''
	for (rowid, host, album, path, views) in db.select('rowid, host, name, path, views', 'albums', 'host = ? and name = ?', [host, album]):
		response += 'album %s (%d views) was ' % (path, views)
		if blacklist:
			try:
				db.insert('blacklist', (host, name, reason, admin))
				response += 'blacklisted and '
			except Exception, e:
				response += 'not blacklisted (%s) and ' % str(e)
		try:
			db.delete('medias', 'album_id = ?', [rowid])
			db.delete('urls',   'album_id = ?', [rowid])
			db.delete('albums', 'rowid = ?',    [rowid])
			rmtree(ospath.join('rips', path))
			response += 'deleted '
		except Exception, e:
			response += 'not deleted (%s) ' % str(e)
		response += '\n'

	db.commit()
	return response


def delete_user(user, blacklist, reason, admin):
	from shutil import rmtree
	from os import path as ospath
	from DB import DB

	db = DB()
	count = db.count('albums', 'author = ?', [user])
	if count == 0:
		raise Exception('user %s does not have any albums' % user)

	response = ''
	for (rowid, host, album, path, views) in db.select('rowid, host, name, path, views', 'albums', 'author = ?', [user]):
		response += 'album %s (%d views) was ' % (path, views)
		if blacklist:
			try:
				db.insert('blacklist', (host, name, reason, admin))
				response += 'blacklisted and '
			except Exception, e:
				response += 'not blacklisted (%s) and ' % str(e)
		try:
			db.delete('medias', 'album_id = ?', [rowid])
			db.delete('urls',   'album_id = ?', [rowid])
			db.delete('albums', 'rowid = ?',    [rowid])
			rmtree(ospath.join('rips', path))
			response += 'deleted '
		except Exception, e:
			response += 'not deleted (%s) ' % str(e)
		response += '\n'

	db.commit()
	return response

