#!/usr/bin/python

from SiteBase  import SiteBase
from SiteImgur import SiteImgur

from json import loads
from re import findall
from time import sleep

class SiteReddit(SiteBase):

	@staticmethod
	def get_host():
		return 'reddit'

	@staticmethod
	def can_rip(url):
		return 'reddit.com' in url

	@staticmethod
	def get_sample_url():
		#return 'http://www.reddit.com/user/ew2d'
		#return 'http://www.reddit.com/user/ew2d/submitted?sort=new'
		#return 'http://www.reddit.com/user/pepsi_next'
		#return 'http://www.reddit.com/r/AmateurArchives/comments/1rtxt6/psa_dont_print_amateurarchives_at_work/'
		return 'http://www.reddit.com/search?q=dreamchaser'

	def sanitize_url(self):
		'''
			Inserts .json to end of URL (but before ?)
		'''
		url = self.url
		if not '.json' in url:
			q = ''
			if '?' in url:
				q = url[url.find('?'):]
				url = url[:url.find('?')]
			if not '.json' in url:
				url = '%s.json' % url
		self.url = '%s%s' % (url, q)

	def get_album_name(self):
		url = self.url
		if '?' in url:
			url = url[:url.find('?')]
		if '#' in url:
			url = url[:url.find('#')]
		albumname = []
		after_reddit = False
		fields = url.split('/')
		for i in xrange(0, len(fields)):
			if 'reddit.com' in fields[i]:
				after_reddit = True
				continue
			if fields[i] == 'user':
				fields[i] = 'u'
			if after_reddit:
				albumname.append(fields[i])
		return '_'.join(albumname)


	def parse(self, struct):
		if not 'kind' in struct:
			return []

		urls = []
		if struct['kind'] == 'Listing':
			for child in struct['data']['children']:
				urls.extend(self.parse(child))

		# Comment
		elif struct['kind'] == 't1':
			# Add all URLs from comment
			urls.extend(findall('(?P<url>https?://[^\s]*imgur.com\/[^\s]+)', struct['data']['body']))
			# Parse replies
			replies = struct['data']['replies']
			if replies != None and type(replies) == dict:
				for reply in replies['data']['children']:
					urls.extend(self.parse(reply))

		# Post
		elif struct['kind'] == 't3':
			data = struct['data']
			if not data['is_self'] and 'imgur.com' in data['url']:
				urls.append(data['url'])
		return urls

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()

		url = self.url
		r = httpy.get(url)
		self.result = [] # Instance field because other methods will add to it (add_urls)
		self.already_got = [] # URLs we've already added
		while True:
			after = None
			json = loads(r)
			if 'error' in json:
				raise Exception('error at %s: %s' % (url, json['error']))
			if type(json) == list:
				for kind in json:
					self.add_urls(self.parse(kind))
				if len(json) > 0 and 'data' in json[0] and 'after' in json[0]['data']:
					after = json[0]['data']['after']
			elif type(json) == dict:
				self.add_urls(self.parse(json))
				if 'data' in json and 'after' in json['data']:
					after = json['data']['after']
			# Stop now if there's no next page
			if after == None or len(self.result) >= 50: # self.MAX_IMAGES_PER_RIP:
				break
			# Load the next page
			url = self.url
			if '?' in url:
				url = '%s&after=%s' % (url, after)
			else:
				url = '%s?after=%s' % (url, after)
			r = httpy.get(url)
			sleep(2)

		return self.result

	def add_url(self, url):
		'''
			Adds relevant URLs to list of URLs
			Gets imgur albums and non-direct imgur links
		'''
		if 'imgur.com' not in url:
			return
		if url in self.already_got:
			return
		self.already_got.append(url)

		url = url.replace('/m.imgur.com', '/imgur.com')
		url = url.replace('http://', '').replace('https://', '')
		url = 'http://%s' % url
		if '?' in url: url = url[:url.find('?')]

		# Album
		if 'imgur.com/a/' in url:
			# http://imgur.com/a/albumid
			#   0  1     2     3    4
			fields = url.split('/')
			if len(fields) > 4:
				sleep(1)
				urls = SiteImgur.get_urls_album_noscript('http://imgur.com/a/%s' % fields[4])
				self.already_got.extend(url)
				self.result.extend(urls)

		# Direct link to image
		elif 'imgur.com/' in url and \
		     (url[-4] == '.' or url[-5] == '.'):
			self.already_got.append(url)
			self.result.append(url)

		# Non-direct link to image
		else:
			sleep(1)
			r = httpy.get(url)
			if 'rel="image_src" href="' in r:
				url = httpy.between(r, 'rel="image_src" href="', '"')[0]
				self.already_got.append(url)
				self.result.append(url)

	def add_urls(self, urls):
		for url in urls:
			self.add_url(url)

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteReddit.get_host():
			return None
		return 'http://reddit.com/%s' % '/'.join(fields[1:])

	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check ripper gets all images in an album
		url = SiteReddit.get_sample_url()
		s = SiteReddit(url)
		urls = s.get_urls()
		for (i, url) in enumerate(urls):
			print i, url
		expected = 10
		if len(urls) < expected:
			raise Exception('expected at least %d images, got %d. url: %s' % (expected, len(urls), url))

if __name__ == '__main__':
	SiteReddit.test()
