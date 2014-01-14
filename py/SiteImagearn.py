#!/usr/bin/python

from SiteBase import SiteBase

class SiteImagearn(SiteBase):

	@staticmethod
	def get_host():
		return 'imagearn'

	@staticmethod
	def can_rip(url):
		return 'imagearn.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://imagearn.com/image.php?id=24580948'

	def sanitize_url(self):
		if '/image.php?id=' in self.url:
			from Httpy import Httpy
			httpy = Httpy()
			r = httpy.get(self.url)
			if not 'View complete gallery: <a href="' in r:
				raise Exception('no gallery found at %s' % self.url)
			self.url = 'http://imagearn.com/%s' % httpy.between(r, 'View complete gallery: <a href="', '"')[0]
		if not '/gallery.php?id=' in self.url:
			raise Exception('expected /gallery.php?id= not found in URL')

	def get_album_name(self):
		gid = self.url.split('/gallery.php?id=')[1]
		if '#' in gid: gid = gid.split('#')[0]
		if '?' in gid: gid = gid.split('?')[0]
		if '&' in gid: gid = gid.split('&')[0]
		return gid

	def get_urls(self):
		r = self.httpy.get(self.url)
		result = []
		album_name = self.get_album_name()
		for img in self.httpy.between(r, 'view this image"><img src="', '"'):
			after = img.split('imagearn.com/')[1]
			link = 'http://img.imagearn.com/imags/%s' % after
			result.append(link)
		return result

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteImagearn.get_host():
			return None
		return 'http://imagearn.com/gallery.php?gid=' % fields[1]

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteImagearn.get_sample_url()
		s = SiteImagearn(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	SiteImagearn.test()
