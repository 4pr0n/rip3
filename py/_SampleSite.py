#!/usr/bin/python

'''
	Skeleton class for site ripper.
	Contains documentation on all required/useful methods.
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
			StatusManager.py uses the results of this method to show what rippers are working/broken on the main page

			Returns:
				None - if ripper is working as expected
				str - Warning message if the ripper may not be working properly.

			Raises:
				Exception - if ripper is definitely broken. Exception message is used to display on site.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://hostname.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			# Raise exception because the site is *very* broken, definitely can't rip from it if we can't hit the home page.
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = _SampleSite.get_sample_url()
		s = _SampleSite(url)
		urls = s.get_urls()
		expected = 10
		if len(urls) < expected:
			# Returning non-None string since this may be a transient error.
			# Maybe the album was deleted but the ripper is working as expected.
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		# Returning None because the ripper is working as expected. No issues found.
		return None

if __name__ == '__main__':
	_SampleSite.test()
