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
	if   method == 'get_rips_by_user':   return get_rips_by_user(keys)
	elif method == 'count_rips_by_user': return count_rips_by_user(keys)
	elif method == 'rip_album':          return rip_album(keys)
	elif method == 'get_album_info':     return get_album_info(keys)
	elif method == 'get_album_progress': return get_album_progress(keys)
	elif method == 'get_album':          return get_album(keys)
	elif method == 'get_album_urls':     return get_album_urls(keys)
	elif method == 'generate_zip':       return generate_zip(keys)
	elif method == 'get_albums':         return get_albums(keys)
	else: return err('unsupported method: %s' % method)


def get_rips_by_user(keys):
	from py.Queries import Queries
	user = keys.get('user', environ.get('REMOTE_ADDR', '0.0.0.0'))
	return Queries.get_rips_by_user(user)


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

	count = count_rips_by_user(keys)['count']
	if count > MAX_RIPS:
		return err('a maximum of %d active rips are allowed at any time. you currently have %d' % (MAX_RIPS, count))

	url = keys['url']
	try:
		from py.SiteBase import SiteBase
		Ripper = SiteBase.get_ripper(url)
		ripper = Ripper(url)
		return ripper.start()
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
	return {
		'album'      : keys['album'],
		'total'      : total,
		'pending'    : pending,
		'completed'  : completed,
		'errored'    : errored,
		'inprogress' : inprogress,
		'elapsed'    : elapsed
	}
	
def get_album_info(keys):
	if not 'album' in keys:
		return err('album required')
	q = '''
		select 
			name, url, host, ready, filesize, created, modified, count, zip, views, metadata
		from albums
		where path like ?
	'''
	from py.DB import DB
	db = DB()
	cur = db.conn.cursor()
	curexec = cur.execute(q, [ keys['album'] ])
	one = curexec.fetchone()
	if one == None:
		return err('album not found')
	(name, url, host, ready, filesize, created, modified, count, zipfile, views, metadata) = one
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
			'thumb'    : 'rips/%s/thumbs/%s' % (path, thumb),
			'twidth'   : twidth,
			'theight'  : theight,
			'metadata' : metadata
		})
	cur.close()
	# Update modified time
	from time import gmtime
	from calendar import timegm
	db.update('albums', 'modified = ?', 'path like ?', [ timegm(gmtime()), keys['album'] ])
	db.commit()
	return response

def get_album_urls(keys):
	if not 'album' in keys:
		return err('album required')
	source = keys.get('source', 'rarchives')
	if source == 'site':
		column = 'url'
	else:
		column = 'image_name'
	q = '''
		select %s
		from medias
		where album_id in (select rowid from albums where path like ?)
	''' % column
	from py.DB import DB
	db = DB()
	cur = db.conn.cursor()
	curexec = cur.execute(q, [ keys['album'] ])
	result = []
	for (url, ) in curexec:
		if source != 'site':
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

	orderby = keys.get('order', None)
	ascdesc = keys.get('sort', None)

	wheres = []
	values = []
	if host != None:
		wheres.append('host like ?')
		values.append(host)
	if author != None:
		wheres.append('author like ?')
		values.append(author)
	where = ''
	if len(wheres) > 0:
		where = 'where %s' % ' AND '.join(wheres)

	if orderby == None or orderby not in ['accessed', 'created', 'host', 'reports', 'count', 'views']:
		orderby = 'accessed'
		ascdesc = 'desc'
	else:
		if ascdesc == None or ascdesc not in ['asc', 'desc']:
			ascdesc = 'desc'
	q = '''
		select
			a.host, a.name, a.path, a.count, a.zip, a.reports,
			type, image_name, width, height, thumb_name, t_width, t_height
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
	for (host, name, path, count, zipfile, reports, mediatype, image, w, h, thumb, tw, th) in curexec:
		d = get_key_from_dict_list(result, path)
		if not 'preview' in d[path]:
			d[path] = {
				'host' : host,
				'name' : name,
				'count' : count,
				'zip' : zipfile,
				'reports' : reports,
				'preview' : []
			}
		d[path]['preview'].append({
				'image' : '/'.join(['rips', path, image]),
				'type' : mediatype,
				'width' : w,
				'height' : h,
				'thumb' : '/'.join(['rips', path, 'thumbs', thumb]),
				't_width' : tw,
				't_height' : th
			})
	return result

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


###################
# HELPER METHODS

def err(error, tb=None):
	response = {'error': error}
	if tb != None:
		response['trace'] = tb.replace('\n', '<br>').replace(' ', '&nbsp;')
	return response

def is_admin():
	db = DB()
	the_password = db.get_config('admin_password')
	cookies = get_cookies()
	return 'rip_admin_password' in cookies and \
	         cookies['rip_admin_password'] == the_password

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

