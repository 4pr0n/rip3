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
		#return 'http://www.reddit.com/user/ew2d/submitted?sort=top'
		#return 'http://www.reddit.com/user/pepsi_next'
		#return 'http://www.reddit.com/user/pepsi_next/submitted'
		#return 'http://www.reddit.com/user/pepsi_next/submitted?sort=top'
		#return 'http://www.reddit.com/user/pepsi_next/?sort=top'
		#return 'http://www.reddit.com/r/AmateurArchives/comments/1rtxt6/psa_dont_print_amateurarchives_at_work/'
		#return 'http://www.reddit.com/search?q=dreamchaser'
		#return 'http://www.reddit.com/search?q=../../etc/passwd'
		#return 'http://en.reddit.com/r/RealGirls/top?t=all'
		return 'http://www.reddit.com/r/AmateurArchives/comments/186q1m/onceavirgin_24_pics/'
		#return 'http://www.reddit.com/r/gonewild/search?q=first+time&restrict_sr=on&sort=relevance&t=all'
		#return 'http://www.reddit.com/r/gonewild/search?q=first+time&restrict_sr=off&sort=relevance&t=all'

	def sanitize_url(self):
		'''
			Inserts .json to end of URL (but before ?)
		'''
		url = self.url
		q = ''
		if not '.json' in url:
			if '?' in url:
				q = url[url.find('?'):]
				url = url[:url.find('?')]
			if not '.json' in url:
				url = '%s.json' % url
		self.url = '%s%s' % (url, q)

	def get_album_name(self):
		url = self.url
		url = url[url.find('reddit.com/')+len('reddit.com/'):]
		url = url.replace('.json', '')
		url = url.replace('/?', '?')
		restrict_sr = True
		extra = ''
		if '?t=' in url:
			# Get top sort
			extra = url[url.find('?t=')+3:]
		elif '?sort=' in url:
			# Get sort
			extra = url[url.find('?sort=')+6:]
		elif '?q=' in url:
			# Get query
			extra = url[url.find('?q=')+3:]
			restrict_sr = 'restrict_sr=on' in url
		if '&' in extra: extra = extra.split('&')[0]

		if '?' in url: url = url.split('?')[0]
		if '#' in url: url = url.split('#')[0]

		albumname = []
		after_reddit = False
		fields = url.split('/')
		if len(fields) > 4:
			fields = fields[0:4]
		for i in xrange(0, len(fields)):
			if i >= len(fields): break
			if fields[i] == 'user':
				fields[i] = 'u'
			if fields[i] == 'comments':
				fields[i] = 'c'
			if not restrict_sr and fields[i] == 'r':
				fields.pop(i)
			else:
				albumname.append(SiteBase.fs_safe(fields[i]))
		if extra != '':
			albumname.append(SiteBase.fs_safe(extra))
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
			urls.extend(findall('(?P<url>https?://[^\s]*imgur.com\/[^\s\)\]]+)', struct['data']['body']))
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
		url = self.url
		r = self.httpy.get(url)
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
			if after == None or len(self.result) >= self.MAX_IMAGES_PER_RIP:
				break
			# Load the next page
			url = self.url
			if '?' in url:
				url = '%s&after=%s' % (url, after)
			else:
				url = '%s?after=%s' % (url, after)
			r = self.httpy.get(url)
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
				try:
					urls = SiteImgur.get_urls_album_noscript('http://imgur.com/a/%s' % fields[4])
				except Exception, e:
					# Failed to get urls, stop.
					return

				for u in urls:
					if u in self.already_got:
						continue
					self.result.append(u)

		# Direct link to image
		elif 'imgur.com/' in url and \
		     (url[-4] == '.' or url[-5] == '.'):
			if not url in self.already_got:
				self.already_got.append(url)
				self.result.append(url)

		# Non-direct link to image
		else:
			# XXX Assume all links are jpgs and already at full-res
			imgid = url[url.find('imgur.com/')+len('imgur.com/'):]
			if '/' in imgid: imgid = imgid.split('/')[0]
			if '?' in imgid: imgid = imgid.split('?')[0]
			if '#' in imgid: imgid = imgid.split('#')[0]
			url = 'http://i.imgur.com/%s.jpg' % imgid
			if not url in self.already_got:
				self.already_got.append(url)
				self.result.append(url)
			'''
			# This code gets the real URL, but can be expensive if we do it hundreds of times in 1 request.
			sleep(1)
			r = self.httpy.get(url)
			if 'rel="image_src" href="' in r:
				url = self.httpy.between(r, 'rel="image_src" href="', '"')[0]
				self.already_got.append(url)
				self.result.append(url)
			'''

	def add_urls(self, urls):
		for url in urls:
			self.add_url(url)
			if len(self.result) >= self.MAX_IMAGES_PER_RIP:
				break

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteReddit.get_host():
			return None

		url = 'http://reddit.com/'
		fields.pop(0)
		if len(fields) > 1 and fields[0] == 'r':
			url += 'r/%s/' % fields[1]
			fields = fields[2:]
		if len(fields) > 1 and fields[0] == 'u' or fields[0] == 'user':
			url += 'user/%s' % fields[1]
			fields = fields[2:]
			while len(fields) > 0:
				if fields[0] in ['comments', 'submitted', 'top']:
					break
				url += '_%s' % fields[0]
				fields.pop(0)
			url += '/'
			if len(fields) > 0 and fields[0] == 'top':
				url += '?sort=top'
				fields.pop(0)
		if len(fields) > 1 and fields[0] == 'search':
			url += 'search?q=%s' % fields[1]
			fields = fields[2:]
		if len(fields) > 1 and fields[0] == 'c':
			url += 'comments/%s/' % fields[1]
			fields = fields[2:]
		if len(fields) > 0 and fields[0] in ['top']:
			url += '%s/' % fields[0]
			fields = fields[1:]
			if len(fields) > 0:
				url += '?t=%s' % '_'.join(fields)
		if len(fields) > 0 and fields[0] in ['submitted', 'comments']:
			url += '%s/' % fields[0]
			fields = fields[1:]
			if len(fields) > 0:
				url += '?sort=%s' % '_'.join(fields)
		return url

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
		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)
		return None

if __name__ == '__main__':
	SiteReddit.test()
