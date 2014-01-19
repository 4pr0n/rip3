#!/usr/bin/python

from SiteBase import SiteBase

class SiteAnonib(SiteBase):

	@staticmethod
	def get_host():
		return 'anonib'

	@staticmethod
	def get_sample_url():
		return 'http://www.anonib.com/on/res/1284.html'

	@staticmethod
	def can_rip(url):
		return 'anonib.com' in url and '/res/' in url

	def sanitize_url(self):
		self.url = self.url.replace('+50.html', '.html').replace('-100.html', '.html')
		self.url = self.url.split('#')[0]
		self.url = self.url.split('?')[0]
		return self.url # No sanitization needed

	def get_album_name(self):
		# http://www.anonib.com/on/res/1284+50.html
		#   0  1        2       3   4      5
		fields = self.url.split('/')
		return '%s-%s' % (fields[3], fields[5].replace('.html', ''))

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()

		r = httpy.get(self.url)
		result = []
		for link in httpy.between(r, '/img.php?path=', '"'):
			result.append(link)
		return result

	@staticmethod
	def get_url_from_album_path(album):
		# anonib_tblr-34871
		# http://www.anonib.com/tblr/res/34871.html#i34871
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteAnonib.get_host():
			return None
		subfields = fields[1].split('-')
		return 'http://anonib.com/%s/res/%s.html' % (subfields[0], subfields[1])

	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://anonib.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		
		url = 'http://www.anonib.com/on/res/1284+50.html'
		s = SiteAnonib(url)
		urls = s.get_urls()
		expected = 35
		if len(urls) < expected:
			return 'expected %d images, got %d. url: %s' % (expected, len(urls), url)
		return None

if __name__ == '__main__':
	SiteAnonib.test()
