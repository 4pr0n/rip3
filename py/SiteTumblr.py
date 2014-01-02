#!/usr/bin/python

from SiteBase import SiteBase

from json import loads
from time import sleep

class SiteTumblr(SiteBase):

	@staticmethod
	def get_host():
		return 'tumblr'

	@staticmethod
	def can_rip(url):
		return 'tumblr.com' in url

	@staticmethod
	def get_sample_url():
		return 'http://galaxiesspinperfectly.tumblr.com/post/28457572012/thegirlcrushing-lolfuckthis-had-a-hangover'
		#return 'http://kittykin5.tumblr.com/'
		#return 'http://topinstagirls.tumblr.com/tagged/berlinskaya'

	def sanitize_url(self):
		# Strip http and extraneous stuff
		url = self.url.replace('http://', '').replace('https://', '')
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]

		fields = url.split('/')
		user = fields[0].split('.')[0]

		# Post
		if '.tumblr.com/post/' in url:
			post = fields[2]
			url = 'http://%s.tumblr.com/post/%s' % (user, post)

		# Tagged
		elif '.tumblr.com/tagged/' in url:
			tag = fields[2]
			url = 'http://%s.tumblr.com/tagged/%s' % (user, tag)

		# Account
		elif fields[0].count('.') == 2 and fields[0].split('.')[0] != 'www':
			url = 'http://%s.tumblr.com/' % user

		else:
			raise Exception('unable to rip tumblr url: %s' % self.url)

		self.url = url

	def get_album_name(self):
		# Strip http
		url = self.url.replace('http://', '')
		fields = url.split('/')
		self.user = fields[0].split('.')[0]
		# Post
		if '.tumblr.com/post/' in url:
			self.post_type = 'post'
			post = fields[2]
			return '%s_post_%s' % (self.user, post)
		# Tagged
		elif '.tumblr.com/tagged/' in url:
			self.post_type = 'tagged'
			tag = fields[2]
			return '%s_tagged_%s' % (self.user, tag)
		# Account
		elif fields[0].count('.') == 2 and fields[0].split('.')[0] != 'www':
			self.post_type = 'account'
			return '%s' % self.user

	def get_api_url(self, offset=0):
		if self.post_type == 'post':
			postid = self.url.split('/')[-1]
			return 'http://api.tumblr.com/v2/blog/%s.tumblr.com/posts?id=%s&api_key=%s' % (self.user, postid, self.api_key)
		url  = 'http://api.tumblr.com/v2/blog/%s' % self.user
		url += '.tumblr.com/posts/photo'
		url += '?api_key=%s' % self.api_key
		url += '&offset=%d' % offset
		if self.post_type == 'tagged':
			tag = self.url.split('/')[-1]
			tag = tag.replace('-', '+')
			tag = tag.replace('_', '%20')
			url += '&tag=%s' % tag
		return url

	def get_urls(self):
		self.api_key = self.db.get_config('tumblr_key')
		if self.api_key == None:
			raise Exception('unable to rip album (%s), tumblr key not found in database' % self.url)

		from Httpy import Httpy
		httpy = Httpy()

		result = []
		offset = 0
		while True:
			url = self.get_api_url(offset=offset)
			r = httpy.get(url)
			json = loads(r)
			if not 'response' in json or not 'posts' in json['response']:
				#raise Exception('no posts found at %s' % self.url)
				break

			posts = json['response']['posts']
			if len(posts) == 0: break

			for post in posts:
				for photos in post['photos']:
					result.append(photos['original_size']['url'])
			if self.post_type == 'post': break
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
			offset += 20
			sleep(1)
		return result

	@staticmethod
	def get_url_from_album_path(album):
		# tumblr_user[_(tagged|post)_id]
		# http://[user].tumblr.com[/(tagged|post)/id]
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteTumblr.get_host():
			return None
		if len(fields) == 2:
			return 'http://%s.tumblr.com/archive' % fields[1]
		if len(fields) == 4:
			return 'http://%s.tumblr.com/%s/%s' % (fields[1], '/'.join(fields[2:3]))
		return None


	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://api.tumblr.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = SiteTumblr.get_sample_url()
		s = SiteTumblr(url)
		urls = s.get_urls()
		expected = 4
		if len(urls) < expected:
			raise Exception('expected at least %d images, got %d. url: %s' % (expected, len(urls), url))

if __name__ == '__main__':
	SiteTumblr.test()
