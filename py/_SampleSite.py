#!/usr/bin/python

'''
	Skeleton class for site ripper
'''
from SiteBase import SiteBase

class _SampleSite(SiteBase):

	@staticmethod
	def get_host():
		'''
			Returns name of site, no TLD (.com, .net) required
		'''
		return 'hostname'

	@staticmethod
	def can_rip(url):
		'''
			Checks if this ripper can rip a URL.
		'''
		return 'hostname.com' in url and '/some_folder/' in url

	@staticmethod
	def get_sample_url():
		'''
			Sample URL to display and use for testing
		'''
		return 'http://hostname.com/index'

	def sanitize_url(self):
		'''
			Do anything special to the URL before starting.
		'''
		self.url = self.url.lower() # Example

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
		result = []
		for link in httpy.between(r, '<img src="', '"'):
			link = 'http://hostname.com%s' % link
			result.append(link)
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
		return result

	@staticmethod
	def get_url_from_album_path(album):
		'''
			For divining a url based on the album name
		'''
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != _SampleSite.get_host():
			return None
		# Return url of album (if possible)

	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://hostname.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = _SampleSite.get_sample_url()
		s = _SampleSite(url)
		urls = s.get_urls()
		expected = 10
		if len(urls) < expected:
			raise Exception('expected at least %d images, got %d. url: %s' % (expected, len(urls), url))

if __name__ == '__main__':
	_SampleSite.test()
