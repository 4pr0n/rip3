#!/usr/bin/python

from SiteBase import SiteBase

class SiteNfsfw(SiteBase):

	@staticmethod
	def get_host():
		return 'nfsfw'

	@staticmethod
	def can_rip(url):
		return 'nfsfw.com/' in url

	@staticmethod
	def get_sample_url():
		#return 'http://nfsfw.com/gallery/v/Emily+Ratajkowski/'
		#return 'http://nfsfw.com/gallery/v/HipBows/'
		return 'http://nfsfw.com/gallery/v/dirtyberd/'

	def sanitize_url(self):
		if not '/gallery/' in self.url:
			raise Exception('expected /gallery/ not found in URL')
		self.url = self.url.split('?')[0]
		self.url = self.url.split('#')[0]
		self.url = self.url.split('&')[0]
		if self.url.endswith('/'): self.url = self.url[:-1]

	def get_album_name(self):
		album = self.url.split('/')[-1]
		return SiteBase.fs_safe(album)

	def get_urls(self):
		page = 1
		result = []
		while True:
			r = self.httpy.get('%s/?g2_page=%d' % (self.url, page))
			if not 'img src="/gallery/d/' in r:
				break
			for img in self.httpy.between(r, 'img src="/gallery/d/', '"'):
				# from: 45925-3/nfsfw+_20_.jpg
				# to:   45926-3/nfsfw+_20_.jpg
				fields = img.split('-')
				f1 = int(fields[0]) + 1
				result.append('http://nfsfw.com/gallery/d/%d-%s' % (f1, '-'.join(fields[1:])))

			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
			# Next page
			page += 1
			if 'g2_page=%d' % page not in r:
				break

		return result
		
	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteNfsfw.get_host():
			return None
		return 'http://nfsfw.com/gallery/v/%s.html' % '/'.join(fields[1:])

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteNfsfw.get_sample_url()
		s = SiteNfsfw(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	SiteNfsfw.test()

