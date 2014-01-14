#!/usr/bin/python

from SiteBase import SiteBase

class SiteChickupload(SiteBase):

	@staticmethod
	def get_host():
		return 'chickupload'

	@staticmethod
	def can_rip(url):
		return 'http://chickupload.com' in url

	@staticmethod
	def get_sample_url():
		return 'http://chickupload.com/gallery/106023/Z64FYY7Q'

	def sanitize_url(self):
		url = self.url
		while url.endswith('/'): url = url[:-1]
		if '/gallery/' in url:
			if not len(url.split('/gallery/')[1].split('/')) == 2:
				raise Exception('expected /gallery/XXX/YYY not found')
		if '/showpicture/' in url:
			if not len(url.split('/showpicture/')[1].split('/')) == 3:
				raise Exception('expected /showpicture/###/XXX/YYY not found')
		self.url = url

	def get_album_name(self):
		return '_'.join(self.url.split('/')[5:])

	def get_urls(self):
		r = self.httpy.get(self.url)
		result = []
		for (index, link) in enumerate(self.httpy.between(r, 'img src="http://', '"')):
			link = 'http://%s' % link.replace('/thumb', '/full/%03d.jpg' % index)
			result.append(link)
		return result

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteChickupload.get_host():
			return None
		if len(fields) == 3:
			return 'http://chickupload.com/gallery/%s' % '/'.join(fields[1:])
		elif len(fields) == 4:
			return 'http://chickupload.com/showpicture/%s' % '/'.join(fields[1:])
		return None

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteChickupload.get_sample_url()
		s = SiteChickupload(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 7
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	SiteChickupload.test()
