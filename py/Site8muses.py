#!/usr/bin/python

'''
	Skeleton class for site ripper
'''
from SiteBase import SiteBase

class Site8muses(SiteBase):

	@staticmethod
	def get_host():
		'''
			Returns name of site, no TLD (.com, .net) required
		'''
		return '8muses'

	@staticmethod
	def can_rip(url):
		'''
			Checks if this ripper can rip a URL.
		'''
		return '8muses.com' in url and '/index/' in url

	def sanitize_url(self):
		'''
			Do anything special to the URL before starting.
		'''
		return self.url # No sanitization needed

	def get_album_name(self):
		'''
			Returns unique album name (unique to this class' host name)
		'''
		return self.url.split('/')[-1]

	def get_urls(self):
		'''
			Returns list of URLs from album. Does not download them.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		r = httpy.get(self.url)
		chunks = httpy.between(r, '<article class="', '</article>')
		if len(chunks) == 0:
			raise Exception('unable to find "article class" at %s '% self.url)
		r = chunks[0]
		result = []
		for link in httpy.between(r, '<a href="', '"'):
			if link.startswith('//'):
				link = 'http:%s' % link
			link = link.replace(' ', '%20')
			result.append(link)
		return result

	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://8muses.com/'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = 'http://www.8muses.com/index/category/hotassneighbor7'
		s = Site8muses(url)
		urls = s.get_urls()
		expected = 21
		if len(urls) != expected:
			raise Exception('expected %d images, got %d. url: %s' % (expected, len(urls), url))

if __name__ == '__main__':
	Site8muses.test()
