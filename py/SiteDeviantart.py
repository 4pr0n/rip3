#!/usr/bin/python

from SiteBase import SiteBase

from threading import Thread
from time import sleep

class SiteDeviantart(SiteBase):

	@staticmethod
	def get_host():
		return 'deviantart'

	@staticmethod
	def can_rip(url):
		return '.deviantart.com' in url and '/gallery/' in url

	@staticmethod
	def get_sample_url():
		# Scraps: http://kurisunoerika.deviantart.com/gallery/?catpath=scraps
		# Gallery: http://dusaleev.deviantart.com/gallery/
		# Subgallery: http://nemovalkyrja.deviantart.com/gallery/26563333?catpath=/
		return 'http://nemovalkyrja.deviantart.com/gallery/26563333?catpath=/'

	def sanitize_url(self):
		self.url = 'http://%s' % self.url.replace('http://', '').replace('https://', '')
		user = self.url.split('/')[2].split('.')[0]
		if '/gallery/' in self.url:
			if self.url.endswith('/gallery/'):
				# Root gallery, get all of it
				self.url += '?catpath=/'
			else:
				# Specific gallery, strip out extraneous stuff
				pass
		self.url = self.url # No sanitization needed

	def get_album_name(self):
		url = self.url
		user = url.split('/')[2].split('.')[0]
		subdir = ''
		if 'catpath=scraps' in url:
			subdir = '_scraps'
		elif '/gallery/' in url:
			# http://user.devinatart.com/gallery/[gallery]
			#   0  1          2             3        4
			if '?' in url: url = url[:url.find('?')]
			if '#' in url: url = url[:url.find('#')]
			fields = url.split('/')
			while '' in fields: fields.remove('')
			if len(fields) == 5:
				# Sub-gallery
				subdir = '_%s' % fields[4]
		return '%s%s' % (user, subdir)

	@staticmethod
	def get_url_from_album_path(album):
		# Format: deviantart_user[_galleryid|_scraps]
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteDeviantart.get_host():
			return None
		if len(fields) == 2:
			return 'http://%s.deviantart.com/gallery/?catpath=/' % fields[1]
		if len(fields) == 3:
			if fields[2] == 'scraps':
				return 'http://%s.deviantart.com/gallery/?catpath=scraps' % fields[1]
			return 'http://%s.deviantart.com/gallery/%s?catpath=/' % (fields[1], fields[2])
		
		# Return url of album (if possible)
		

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()

		self.thread_count = 0
		self.max_threads  = 3
		r = httpy.get(self.url)
		result = []
		already_got = []
		while True:
			for chunk in httpy.between(r, '<a class="thumb', '>'):
				if not 'href="' in chunk: continue
				link = httpy.between(chunk, 'href="', '"')[0]
				if link in already_got:
					continue
				already_got.append(link)
				# Get image from page
				while self.thread_count >= self.max_threads:
					sleep(0.1)
				self.thread_count += 1
				t = Thread(target=self.get_url_from_page, args=(httpy, result, link,))
				t.start()
			# Go to next page
			nexts = httpy.between(r, '<li class="next">', '</li>')
			if len(nexts) == 0 or not 'href"' in nexts[0]:
				break
			next_page = httpy.between(nexts[0], 'href="', '"')[0]
			if not 'offset=' in next_page:
				break
			r = httpy.get(next_page)
		while self.thread_count > 0:
			sleep(0.1)
		return result

	def get_url_from_page(self, httpy, result, page):
		r = httpy.get(page)
		self.thread_count -= 1
		d = [
			('id="download-button"',      '<',     'href="',             '"'),
			('ResViewSizer_img',          '>',     'src="',              '"'),
			('name="og:image" content="', '"',      None,                None),
			('<div class="preview"',      '</div>', '" data-super-img="', '"'),
			('<div class="preview"',      '</div>', '" data-src="', '"')
		]
		for (begin1, end1, begin2, end2) in d:
			if begin1 in r and end1 in r:
				chunk = httpy.between(r, begin1, end1)[0]
				if begin2 == None:
					result.append(self.thumb_to_full(chunk))
					return
				print 'XXX: %s and %s in %s' % (begin1, end1, page)
				print 'XXX: CHUNK=\n%s' % chunk
				if begin2 in chunk and end2 in chunk:
					url = httpy.between(chunk, begin2, end2)[0]
					result.append(self.thumb_to_full(url))
					return
				print 'XXX: %s and %s NOT in %s' % (begin2, end2, page)
		# Unable to get image at page
		raise Exception('failed to get image at %s' % page)

	def thumb_to_full(self, url):
		return url.replace('://th', '://fc').replace('/150/i/', '/i/').replace('/150/f/', '/f/')

	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://deviantart.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = SiteDeviantart.get_sample_url()
		s = SiteDeviantart(url)
		urls = s.get_urls()
		print urls
		expected = 10
		if len(urls) < expected:
			raise Exception('expected at least %d images, got %d. url: %s' % (expected, len(urls), url))

if __name__ == '__main__':
	SiteDeviantart.test()
