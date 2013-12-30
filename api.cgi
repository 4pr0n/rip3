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
		print ripper.get_host()
		#return ripper.start()
	except Exception, e:
		return err(str(e), tb=format_exc())


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

