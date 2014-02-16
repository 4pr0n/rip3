#!/usr/bin/python

MAX_RIPS = 20

from os        import environ
from traceback import format_exc # Stack traces
from json      import dumps
from cgi       import FieldStorage # Query keys
from cgitb     import enable as cgi_enable; cgi_enable() # for debugging
from urllib    import unquote

def main():
	keys = get_keys()
	if not 'method' in keys:
		raise Exception('unspecified method')
	method = keys['method']
	if   method == 'count_rips_by_user': return count_rips_by_user(keys)
	elif method == 'rip_album':          return rip_album(keys)
	elif method == 'get_album_info':     return get_album_info(keys)
	elif method == 'get_album_progress': return get_album_progress(keys)
	elif method == 'get_album':          return get_album(keys)
	elif method == 'get_album_urls':     return get_album_urls(keys)
	elif method == 'generate_zip':       return generate_zip(keys)
	elif method == 'get_albums':         return get_albums(keys)
	elif method == 'rip_video':          return rip_video(keys)
	elif method == 'get_admin':          return {'admin': get_admin() }
	elif method == 'report_album':       return report_album(keys)
	elif method == 'ban_user':           return ban_user(keys)
	elif method == 'warn_user':          return warn_user(keys)
	elif method == 'delete_album':       return delete_album(keys)
	elif method == 'delete_user':        return delete_user(keys)
	else: return err('unsupported method: %s' % method)


def count_rips_by_user(keys):
	user = keys.get('user', environ.get('REMOTE_ADDR', '0.0.0.0'))
	from py.DB import DB
	db = DB()
	count = db.count('albums', 'author like ?', [user])
	return {
		'count' : count,
		'user'  : user
	}


def rip_album(keys):
	if not 'url' in keys:
		return err('url required')

	from py.DB import DB
	db = DB()

	max_rips = db.get_config('max_rips')
	if max_rips == None:
		max_rips = MAX_RIPS

	count = count_rips_by_user(keys)['count']
	if count > max_rips:
		return err('a maximum of %d active rips are allowed at any time. you currently have %d' % (max_rips, count))

	url = keys['url']
	try:
		from py.SiteBase import SiteBase
		Ripper = SiteBase.get_ripper(url)
		ripper = Ripper(url)

		# Blacklist check
		host = ripper.get_host()
		album = ripper.get_album_name()
		blacklist_count = db.count('blacklist', 'host like ? and album like ?', [host, album])
		if blacklist_count > 0:
			return err('that album (%s_%s) is blacklisted' % (host, album))

		return ripper.start()
	except Exception, e:
		e = format_exc()  # just to retain original error.	
		try:
			from py.VideoBase import VideoBase
			Ripper = VideoBase.get_ripper(url)			
			ripper = Ripper(url)
			return ripper.rip_video()
		except Exception, ex:
			pass
		return err(str(e), tb=e)

def rip_video(keys):
	if not 'url' in keys:
		return err('url required')

	url = keys['url']
	try:
		from py.VideoBase import VideoBase
		Ripper = VideoBase.get_ripper(url)
		ripper = Ripper(url)
		return ripper.rip_video()
	except Exception, e:
		return err(str(e), tb=format_exc())

##############
# SINGLE ALBUM

def get_album_progress(keys):
	if not 'album' in keys:
		return err('album required')
	from py.DB import DB
	from time import gmtime
	from calendar import timegm
	db = DB()
	(rowid,created) = db.select('rowid, created', 'albums', 'path like ?', [keys['album']]).fetchone()
	total      = db.select_one('count', 'albums', 'rowid = ?', [rowid])
	pending    = db.count('urls', 'album_id = ?', [rowid])
	completed  = db.count('medias', 'album_id = ? and valid = 1', [rowid])
	errored    = db.count('medias', 'album_id = ? and error is not null', [rowid])
	inprogress = total - pending - completed - errored
	elapsed    = timegm(gmtime()) - created
	totalsize = db.select_one('filesize', 'albums', 'rowid = ?', [rowid])
	return {
		'album'      : keys['album'],
		'total'      : total,
		'pending'    : pending,
		'completed'  : completed,
		'errored'    : errored,
		'inprogress' : inprogress,
		'elapsed'    : elapsed,
		'filesize'   : totalsize
	}


def get_album_info(keys):
	if not 'album' in keys:
		return err('album required')

	q = '''
		select 
			rowid, name, url, host, ready, filesize, created, modified, count, zip, views, metadata, author
		from albums
		where path like ?
	'''
	from py.DB import DB
	db = DB()
	cur = db.conn.cursor()
	curexec = cur.execute(q, [ keys['album'] ])
	one = curexec.fetchone()
	if one == None:
		# Album does not exist
		response = err('album not found')
		response['url'] = get_url_from_path(keys['album'])
		return response

	(rowid, name, url, host, ready, filesize, created, modified, count, zipfile, views, metadata, author) = one
	response = {
		'album_name' : name,
		'url' : url,
		'host' : host,
		'ready' : ready == 1,
		'filesize' : filesize,
		'created' : created,
		'modified' : modified,
		'count' : count,
		'zip' : zipfile,
		'views' : views,
		'metadata' : metadata
	}

	# Update album access time
	from time import gmtime
	from calendar import timegm
	db.update('albums', 'accessed = ?', 'path like ?', [ timegm(gmtime()), keys['album'] ])
	db.update('albums', 'views = views + 1', 'path like ?', [ keys['album'] ])
	db.commit()

	# Check if current user already reported the album
	user   = keys.get('user', environ.get('REMOTE_ADDR', '0.0.0.0'))
	report = db.select_one('message', 'reports', 'album like ? and user like ?', [ keys['album'], user ])
	if report != None:
		response['already_reported'] = report

	# ADMIN functions
	admin_user = get_admin()
	if admin_user != None:
		q = 'select user, message from reports where album like ?'
		reports = []
		curexec = cur.execute(q, [ keys['album'] ])
		for (user, message) in curexec:
			reports.append({
				'ip' : user,
				'message' : message
			})
		response['admin'] = {
			'admin_user' : admin_user,
			'album' : keys['album'],
			'reports' : reports
		}

		author_rips = db.count('albums', 'author = ?', [author])

		q = '''
			select warning_message, warnings, warned, banned, banned_reason, banned_url
			from users
			where ip = ?
		'''
		curexec = cur.execute(q, [author])
		one = curexec.fetchone()
		if one == None:
			response['admin']['user'] = {
				'ip' : author,
				'rip_count' : author_rips,
				'warning_message' : None,
				'warnings' : 0,
				'warn_date' : 0,
				'banned' : False,
				'banned_reason' : None,
				'banned_url' : None
			}
		else:
			(warn_msg, warn_count, warn_date, banned, banned_reason, banned_url) = one
			response['admin']['user'] = {
				'ip' : author,
				'rip_count' : author_rips,
				'warning_message' : warn_msg,
				'warnings' : warn_count,
				'warn_date' : warn_date,
				'banned' : (banned == 1),
				'banned_reason' : banned_reason,
				'banned_url' : banned_url
			}
	cur.close()

	return response


def get_album(keys):
	if not 'album' in keys:
		return err('album required')
	start = int(keys.get('start', '0'))
	count = int(keys.get('count', '10'))
	q = '''
		select
			i_index, medias.url, valid, error, type, image_name, width, height, medias.filesize, thumb_name, t_width, t_height, medias.metadata, albums.path
		from medias inner join albums on medias.album_id = albums.rowid
		where albums.path like ?
		order by i_index asc
		limit %d
		offset %d
	''' % (count, start)
	from py.DB import DB
	db = DB()
	cur = db.conn.cursor()
	curexec = cur.execute(q, [ keys['album'] ])
	response = []
	for (index, url, valid, error, filetype, name, width, height, filesize, thumb, twidth, theight, metadata, path) in curexec:
		if thumb == 'nothumb.png':
			thumb = './ui/images/%s' % thumb
		else:
			thumb = 'rips/%s/thumbs/%s' % (path, thumb)
		response.append({
			'index'    : index,
			'url'      : url,
			'valid'    : valid == 1,
			'error'    : error,
			'type'     : filetype,
			'image'    : 'rips/%s/%s' % (path, name),
			'width'    : width,
			'height'   : height,
			'filesize' : filesize,
			'thumb'    : thumb,
			't_width'  : twidth,
			't_height' : theight,
			'metadata' : metadata
		})
	cur.close()
	return response


def get_album_urls(keys):
	if not 'album' in keys:
		return err('album required')
	source = keys.get('source', 'rarchives')
	if source == 'source':
		column = 'url'
		where = ''
	else:
		column = 'image_name'
		where = 'and medias.error is null'
	q = '''
		select %s
		from medias
		where album_id in (select rowid from albums where path like ?)
		%s
	''' % (column, where)
	from py.DB import DB
	db = DB()
	cur = db.conn.cursor()
	curexec = cur.execute(q, [ keys['album'] ])
	result = []
	for (url, ) in curexec:
		if source != 'source':
			url = 'http://rip.rarchives.com/rips/%s/%s' % (keys['album'], url)
		result.append(url)
	# Also grab pending URLs
	if source == 'site':
		q = '''
			select url
				from urls
				where album_id in (select rowid from albums where path like ?)
		'''
		curexec = cur.execute(q, [ keys['album'] ])
		for (url, ) in curexec:
			result.append(url)
	cur.close()
	return result

def get_albums(keys):
	start   = int(keys.get('start', '0'))
	count   = int(keys.get('count', '6'))
	preview = int(keys.get('preview', '4'))

	host    = keys.get('host', None)
	author  = keys.get('author', None)

	orderby = keys.get('sort', None)
	ascdesc = keys.get('order', None)

	wheres = ['ready = 1']
	values = []
	if host != None:
		wheres.append('host like ?')
		values.append(host)
	if author != None:
		if author == 'mine':
			author = environ.get('REMOTE_ADDR', '0.0.0.0')
		wheres.append('author like ?')
		values.append(author)
	where = ''
	if len(wheres) > 0:
		where = 'where %s' % ' AND '.join(wheres)

	if orderby == None or orderby not in ['accessed', 'created', 'host', 'reports', 'count', 'views']:
		orderby = 'accessed'
	if ascdesc == None or ascdesc not in ['asc', 'desc']:
		ascdesc = 'desc'

	q = '''
		select
			a.host, a.name, a.path, a.count, a.zip, a.reports,
			type, image_name, width, height, thumb_name, t_width, t_height, medias.url, medias.filesize
		from 
			(select
					rowid, host, name, path, count, zip, reports, accessed, modified, created, host, reports, count, views
				from 
					albums 
				%s
				order by %s %s
				limit %d
				offset %d
			) as a
				inner join
			medias
				on medias.album_id = a.rowid
			where i_index <= %d and medias.valid = 1
	''' % (where, orderby, ascdesc, count, start, preview)
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	curexec = cursor.execute(q, values)
	result = []
	admin_user = get_admin()
	for (host, name, path, count, zipfile, reports, mediatype, image, w, h, thumb, tw, th, url, filesize) in curexec:
		d = get_key_from_dict_list(result, path)
		if not 'preview' in d[path]:
			d[path] = {
				'host' : host,
				'name' : name,
				'count' : count,
				'zip' : zipfile,
				'preview' : []
			}
		if thumb == 'nothumb.png':
			thumb = './ui/images/%s' % thumb
		else:
			thumb = '/'.join(['rips', path, 'thumbs', thumb])
		d[path]['preview'].append({
				'image' : '/'.join(['rips', path, image]),
				'type' : mediatype,
				'width' : w,
				'height' : h,
				'thumb' : thumb,
				't_width' : tw,
				't_height' : th,
				'url' : url,
				'filesize' : filesize
			})
		if admin_user != None:
			d[path]['admin'] = {
				'admin_user' : admin_user,
				'album'   : path,
				'reports' : reports
			}
	response = {
		'albums' : result,
		'author' : keys.get('author', None)
	}

	# Provide list of supported sites on first request only
	if int(keys.get('start', '0')) == 0:
		from py.SiteBase import SiteBase
		#           wow
		#                        so 1line
		#   such pythonic
		response['sites'] = [x.get_host() for x in SiteBase.iter_rippers()]
		#                    hexplode
	return response

def get_key_from_dict_list(lst, key):
	for d in lst:
		if key in d:
			return d
	d = {key: {} }
	lst.append(d)
	return d

def generate_zip(keys):
	if not 'album' in keys:
		return err('album required')

	from os import path
	album_path = path.join('rips', keys['album'])
	zip_path = '%s.zip' % album_path
	if path.exists(zip_path):
		return {
			'zip'      : zip_path,
			'filesize' : path.getsize(zip_path)
		}

	if not path.exists(album_path):
		return err('album not found')

	from py.DB import DB
	db = DB()
	if db.count('albums', 'path like ?', [keys['album']]) == 0:
		return err('album not found in database')

	# Album exists, zip does not. Zip it. Zip it good.
	from os      import walk
	from zipfile import ZipFile, ZIP_STORED

	db.update('albums', 'zip = ?', 'path like ?', [zip_path, keys['album'] ])
	db.commit()

	z = ZipFile(zip_path, "w", ZIP_STORED) # Using stored to conserve CPU
	for root, dirs, files in walk(album_path):
		if root.endswith('/thumbs'): continue
		for fn in files:
			absfn = path.join(root, fn)
			zipfn = path.basename(absfn)
			z.write(absfn, zipfn)
	z.close()
	return {
		'zip'      : zip_path,
		'filesize' : path.getsize(zip_path)
	}

def report_album(keys):
	if 'album' not in keys:
		return err('album is required')

	album  = keys['album']
	reason = keys.get('reason', None)
	user   = keys.get('user', environ.get('REMOTE_ADDR', '0.0.0.0'))

	from py.DB import DB
	db = DB()
	if db.count('albums', 'path like ?', [album]) == 0:
		return err('album not found; unable to report')

	previous_reason = db.select_one('message', 'reports', 'album like ? and user like ?', [album, user])
	if previous_reason != None:
		return err('already reported with reason "%s"' % previous_reason)

	db.insert('reports', [album, user, reason])
	db.update('albums', 'reports = reports + 1', 'path like ?', [album])
	db.commit()
	return err('album has been reported. the admins will look into this soon.')


###################
# ADMIN METHODS

def ban_user(keys):
	if get_admin() == None:
		return err('you are not an admin')
	user    = keys.get('user',    None)
	message = keys.get('message', None)
	url     = keys.get('url',     None)
	if user    == None: return err('user required for ban')

	from py.DB import DB
	db = DB()

	if keys.get('unban', False):
		db.update('users', 'banned = 0, banned_reason = NULL', 'ip = ?', [user])
		db.commit()
		return {
			'color'   : 'success',
			'user'    : user,
			'message' : 'user was unbanned'
		}

	if message == None: return err('message required for ban')

	cursor = db.conn.cursor()
	if db.count('users', 'ip = ?', [user]):
		reason = db.select_one('banned_reason', 'users', 'ip = ?', [user])
		if reason != None:
			return {
				'color'   : 'warning',
				'user'    : user,
				'message' : 'user is already banned, reason: "%s"' % reason
			}
		db.update('users', 'banned = 1, banned_reason = ?', 'ip = ?', [message, user])
	else:
		db.insert('users', (user, None, 0, 0, 1, message, url,) )
	db.commit()
	cursor.close()

	return {
		'color'   : 'success',
		'user'    : user,
		'message' : 'user was banned'
	}

def warn_user(keys):
	user    = keys.get('user',    None)
	message = keys.get('message', None)
	url     = keys.get('url',     None)
	if user    == None: return err('user required for warn')

	from py.DB import DB
	db = DB()

	if keys.get('unwarn', False):
		db.update('users', 'warnings = 0, warning_message = NULL, warned = 0', 'ip = ?', [user])
		db.commit()
		return {
			'color'   : 'success',
			'user'    : user,
			'message' : 'warnings were cleared'
		}

	if message == None: return err('message required for warn')

	from time import gmtime
	from calendar import timegm
	cursor = db.conn.cursor()
	if db.count('users', 'ip = ?', [user]):
		warn_message = db.select_one('warning_message', 'users', 'ip = ?', [user])
		if warn_message != None:
			return {
				'color'   : 'warning',
				'user'    : user,
				'message' : 'user is already warned, message: "%s"' % warn_message
			}
		db.update('users', 'warnings = warnings + 1, warning_message = ?, warned = ?', 'ip = ?', [message, timegm(gmtime()), user])
	else:
		db.insert('users', (user, message, 1, timegm(gmtime()), 0, None, None,) )
	db.commit()
	cursor.close()

	return {
		'color'   : 'success',
		'user'    : user,
		'message' : 'user was warned'
	}


def delete_album(keys):
	if not 'host' in keys:
		return err('host is required')
	if not 'album' in keys:
		return err('album is required')
	blacklist = keys.get('blacklist', 'false')
	blacklist = (blacklist == 'true')

	admin = get_admin()
	if admin == None:
		return err('you are not an admin')

	from py.Common import delete_album as common_delete_album
	try:
		response = common_delete_album(keys['host'], keys['album'], blacklist, keys.get('reason', None), admin)
		return {
			'color'   : 'success',
			'message' : response
		}
	except Exception, e:
		return {
			'color' : 'danger',
			'message' : err(str(e))
		}


def delete_user(keys):
	if not 'user' in keys:
		return err('user is required')
	blacklist = keys.get('blacklist', 'false')
	blacklist = (blacklist == 'true')

	admin = get_admin()
	if admin == None:
		return err('you are not an admin')

	from py.Common import delete_user as common_delete_user
	try:
		response = common_delete_user(keys['user'], blacklist, keys.get('reason', None), admin)
		return {
			'color'   : 'success',
			'message' : response.replace('\n', '<br>')
		}
	except Exception, e:
		return {
			'color' : 'danger',
			'message' : err(str(e))
		}

###################
# HELPER METHODS


def err(error, tb=None):
	response = {'error': error}
	if tb != None:
		response['trace'] = tb.replace('\n', '<br>').replace(' ', '&nbsp;')
	return response

def get_admin():
	cookies = get_cookies()
	cookie = cookies.get('rip_admin_password', None)
	if cookie == None:
		return None
	from py.DB import DB
	db = DB()
	user = db.select_one('username', 'admins', 'cookie like ?', [cookie])
	return user

def get_keys(): # Get query keys
	form = FieldStorage()
	keys = {}
	for key in form.keys():
		if form[key].value != 'undefined':
			keys[key] = unquote(form[key].value)
	return keys

""" Returns dict of requester's cookies """
def get_cookies():
	if not 'HTTP_COOKIE' in environ: return {}
	cookies = {}
	txt = environ['HTTP_COOKIE']
	for line in txt.split(';'):
		if not '=' in line: continue
		pairs = line.strip().split('=')
		cookies[pairs[0]] = pairs[1]
	return cookies

def get_url_from_path(path):
	from py.SiteBase import SiteBase
	for ripper in SiteBase.iter_rippers():
		if path.startswith(ripper.get_host()):
			return ripper.get_url_from_album_path(path)
	return None

########################
# ENTRY POINT
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	try:
		print dumps(main(), indent=2)
	except Exception, e:
		print dumps(err(str(e), format_exc()))
	print "\n\n"

