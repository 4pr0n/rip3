#!/usr/bin/python

from SiteBase import SiteBase

class SiteImgur(SiteBase):

	@staticmethod
	def get_host():
		return 'imgur'

	@staticmethod
	def get_sample_url():
		return 'http://imgur.com/a/RdXNa'

	@staticmethod
	def can_rip(url):
		# Album
		if 'imgur.com/a/' in url:
			return True

		# User account
		elif '.imgur.com' in url and \
		     '/www.imgur.com' not in url and \
		     '/m.imgur.com'   not in url and \
		     '/i.imgur.com'   not in url:
			return True

		# Subreddit
		elif 'imgur.com/r/' in url:
			return True

		return False

	@staticmethod
	def test():
		raise Exception('unexpected length of album')

	def sanitize_url(self):
		url = self.url
		if '/m.imgur.com/' in url:
			url = url.replace('/m.imgur.com/', '/imgur.com/')
		if not url.endswith('/'):
			url += '/'
		if 'imgur.com/a/' in url:
			url = 'http://imgur.com/a/%s' % url.split('imgur.com/a/')[1].split('/')[0]
		if 'imgur.com/r/' in url:
			# TODO get sort/time, put in url
			url = 'http://imgur.com/r/%s/%s/%s' % (subreddit, sort, time)
			pass
		self.url = url

		def get_album_name(self):
			# Album
			# User account
			# Subreddit
			pass
	
	@staticmethod
	def get_highest_res(url):
		'''
			Checks if URL is not highest-res version
			Gets highest-res version
			Args:
				url: The imgur URL
			Returns:
				URL to highest-res version of image
		'''
		if not 'h.' in url:
			return url
		temp = url.replace('h.', '.')
		m = self.web.get_meta(temp)
		if 'Content-Length' in m and m['Content-Length'] == '503':
			raise Exception(temp)
		if 'Content-Type' in m and 'image' in m['Content-Type'].lower():
			return temp
		else:
			return url

