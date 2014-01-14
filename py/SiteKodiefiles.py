#!/usr/bin/python

from SiteBase import SiteBase

class SiteKodiefiles(SiteBase):

	@staticmethod
	def get_host():
		return 'kodiefiles'

	@staticmethod
	def can_rip(url):
		return 'kodiefiles.nl/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.kodiefiles.nl/2010/10/ff-eerder-gezien.html'

	def sanitize_url(self):
		self.url = self.url # Nothing

	def get_album_name(self):
		fields = self.url.replace('.html', '').split('kodiefiles.nl/')[1].split('/')
		return '_'.join(fields)

	def get_urls(self):
		r = self.httpy.get(self.url)
		result = []
		for image in self.httpy.between(r, '0" src="', '"'):
			image = image.replace('/tn_', '/').replace('/thumbs/', '/full/')
			result.append(image)
		return result
		
	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteKodiefiles.get_host():
			return None
		return 'http://kodiefiles.nl/%s.html' % '/'.join(fields[1:])

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteKodiefiles.get_sample_url()
		s = SiteKodiefiles(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	SiteKodiefiles.test()
