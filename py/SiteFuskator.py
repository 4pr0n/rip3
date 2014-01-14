#!/usr/bin/python

from SiteBase import SiteBase

class SiteFuskator(SiteBase):

	@staticmethod
	def get_host():
		return 'fuskator'

	@staticmethod
	def can_rip(url):
		return 'fuskator.com' in url

	@staticmethod
	def get_sample_url():
		return 'http://fuskator.com/full/-3DzsbRTrh3/'

	def sanitize_url(self):
		url = self.url
		if '/thumbs/' in url:
			url = url.replace('/thumbs/', '/full/')
		if not '/full/' in url:
			raise Exception('expected /full/ not found in URL')
		self.url = url

	def get_album_name(self):
		return self.url.replace('http://', '').replace('https://', '').split('/')[2]

	def get_urls(self):
		from urllib import unquote
		r = self.httpy.get(self.url)
		if not "baseUrl = unescape('" in r:
			return Exception('expected baseUrl not found at %s' % self.url)
		baseurl = unquote(self.httpy.between(r, "baseUrl = unescape('", "'")[0])
		result = []
		for image in self.httpy.between(r, ".src=baseUrl+'", "'"):
			link = '%s%s' % (baseurl, image)
			result.append(link)
		return result

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteFuskator.get_host():
			return None
		return 'http://fuskator.com/full/%s' % fields[1]

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteFuskator.get_sample_url()
		s = SiteFuskator(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	SiteFuskator.test()
