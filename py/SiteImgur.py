#!/usr/bin/python

class SiteImgur(SiteBase):

	@staticmethod
	def can_rip(url):
		if 'imgur.com/a/' in url:
			return True
		elif '.imgur.com' in url and 
		     '/www.imgur.com' not in url and
		     '/m.imgur.com'   not in url and
		     '/i.imgur.com'   not in url:
			return True
		return False

	def sanitize_url(url):
		if '/m.imgur.com/' in url:
			url = url.replace('/m.imgur.com/', '/imgur.com/')
		if not url.endswith('/'): url += '/'
		if 'imgur.com/a/' in url:
			return 'http://imgur.com/a/%s' % url.split('imgur.com/a/')[1].split('/')[0]
		return url
