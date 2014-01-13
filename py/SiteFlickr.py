#!/usr/bin/python

from SiteBase import SiteBase

class SiteFlickr(SiteBase):

	@staticmethod
	def get_host():
		return 'flickr'

	@staticmethod
	def can_rip(url):
		return 'flickr.com' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.flickr.com/photos/amyjernigan/with/715062304/'

	def sanitize_url(self):
		url = self.url
		if '/photos/' not in url:
			raise Exception('required /photos/ not found in URL')
		users = url.split('/photos/')[1].split('/')[0]
		if len(users) == 0 or users[0] == 'tags':
			raise Exception('invalid flickr album URL')
		self.url = url

	def get_album_name(self):
		'''
			Format: <username>[_<setname>]
		'''
		url = self.url
		sets = ''
		if '/sets/' in url:
			sets = '_%s' % url.split('/sets/')[1].split('/')[0]
		user = url.split('/photos/')[1].split('/')[0]
		return '%s%s' % (user, sets)


	def flickr_signin(self):
		creds = self.db.get_config('flickr_creds')
		if creds == None or ':' not in creds:
			raise Exception('unable to sign in to flickr: no credentials')
		(username, password) = creds.split(':')
		# Get required signin parameters
		r = self.httpy.get('http://www.flickr.com/signin/')
		if not '<form method="post"' in r:
			raise Exception('no post form found at flickr.com/signin/')
		postdata = {
			'passwd_raw' : '',
			'.save'  : '',
			'login'  : username,
			'passwd' : password
		}
		form = self.httpy.between(r, '<form method="post"', '</fieldset>')[0]
		for inp in self.httpy.between(form, '<input type="hidden"', '>'):
			name  = self.httpy.between(inp, 'name="', '"')[0]
			value = self.httpy.between(inp, 'value="', '"')[0]
			postdata[name] = value
		posturl = self.httpy.between(form, 'action="', '"')[0]
		r = self.httpy.post(posturl, postdata=postdata)
		if 'window.location.replace("' not in r:
			raise Exception('failed to sign in to flickr')
		confirmurl = self.httpy.between(r, 'window.location.replace("', '"')[0]
		r = self.httpy.get(confirmurl)
		return True

	def get_urls(self):
		from threading import Thread
		from time import sleep
		from Httpy import Httpy
		httpy = Httpy()

		# Sign in so we can get restricted content
		self.flickr_signin()

		r = httpy.get(self.url)
		self.result = []
		index = 0
		while True:
			for link in self.httpy.between(r, '><a data-track="photo-click" href="', '"'):
				if link == '{{photo_url}}': continue
				link = 'http://www.flickr.com%s' % link
				while not link.endswith('/'):
					link += '/'
				link += 'sizes/o/' # Default to 'original' size

				# Find and download image at this page
				while len(self.threads) >= self.max_threads:
					sleep(0.1) # Wait for threads
				self.threads.append(None)
				t = Thread(target=self.get_url_from_page, args=(link,index,))
				t.start()
				index += 1
				if len(self.result) + len(self.threads) > self.MAX_IMAGES_PER_RIP:
					break

			if len(self.result) + len(self.threads) > self.MAX_IMAGES_PER_RIP:
				break

			# Look for 'next' button
			if 'data-track="next" href="' in r:
				nextpage = self.httpy.between(r, 'data-track="next" href="', '"')[0]
				if not 'flickr.com' in nextpage:
					nextpage = 'http://flickr.com%s' % nextpage
				r = self.httpy.get(nextpage)
			else:
				# No more pages, we're done
				break

		# Wait for threads to finish
		while len(self.threads) > 0:
			sleep(0.1)
		return self.result
	
	def get_url_from_page(self, link, index):
		r = self.httpy.get(link)
		if not '<ol class="sizes-list">' in r:
			# No list of sizes, abort!
			self.threads.pop()
			return
		bestlink = link
		sizechunk = self.httpy.between(r, '<ol class="sizes-list">', '</div>')[0]
		for size in self.httpy.between(sizechunk, '<ol>', '</ol>'):
			if not 'href="' in size:
				# Currently-viewed image
				bestlink = link
			else:
				bestlink = 'http://flickr.com%s' % self.httpy.between(size, 'href="', '"')[0]
		if bestlink != link:
			# Load the page with the best link
			r = self.httpy.get(bestlink)
		image = 'http://farm%s' % self.httpy.between(r, '<img src="http://farm', '"')[0]

		urlinfo = {
			'url'   : image,
			'index' : index
		}
		if 'name="title" content="' in r:
			metadata = self.httpy.between(r, 'name="title" content="', '">')[0]
			if ' | ' in metadata:
				metadata = metadata.split(' | ')[1]
			urlinfo['metadata'] = metadata
		self.result.append(urlinfo)
		self.threads.pop()

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteFlickr.get_host():
			return None
		# Return url of album (if possible)

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://hostname.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = SiteFlickr.get_sample_url()
		s = SiteFlickr(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		# Returning None because the ripper is working as expected. No issues found.
		return None

if __name__ == '__main__':
	SiteFlickr.test()
