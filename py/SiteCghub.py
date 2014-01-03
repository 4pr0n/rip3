#!/usr/bin/python

'''
	Skeleton class for site ripper
'''
from SiteBase import SiteBase

class SiteCghub(SiteBase):

	@staticmethod
	def get_host():
		return 'cghub'

	@staticmethod
	def can_rip(url):
		return '.cghub.com' in url and not 'www.cghub.com' in url and not '//cghub.com' in url

	@staticmethod
	def get_sample_url():
		return 'http://katiedesousa.cghub.com/images/'

	def sanitize_url(self):
		user = self.url[self.url.find('://')+3:self.url.find('.')]
		self.url = 'http://%s.cghub.com/images/' % user

	def get_album_name(self):
		user = self.url[self.url.find('://')+3:self.url.find('.')]
		return user

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()

		url = self.url
		result = []
		while True:
			r = httpy.get(url)
			for chunk in httpy.between(r, '<a name="', '</li>'):
				if not '<img src="' in chunk: continue
				image = httpy.between(chunk, '<img src="', '"')[0]
				image = image.replace('_stream', '_max')
				if image.startswith('//'):
					image = 'http:%s' % image
				result.append(image)
			if '<li class="next"><a href="' in r:
				url = httpy.between(r, '<li class="next"><a href="', '"')[0]
			else:
				break
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
		url = 'http://cghub.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = SiteCghub.get_sample_url()
		s = SiteCghub(url)
		urls = s.get_urls()
		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)
		return None

if __name__ == '__main__':
	SiteCghub.test()
