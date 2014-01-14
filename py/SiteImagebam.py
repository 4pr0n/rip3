#!/usr/bin/python

from SiteBase import SiteBase

class SiteImagebam(SiteBase):

	@staticmethod
	def get_host():
		return 'imagebam'

	@staticmethod
	def can_rip(url):
		return 'imagebam.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.imagebam.com/gallery/3e4u10fk034871hs6idcil6txauu3ru6/'

	def sanitize_url(self):
		if '/image/' in self.url:
			from Httpy import Httpy
			httpy = Httpy()
			r = httpy.get(self.url)
			if not "class='gallery_title'><a href='" in r:
				raise Exception('no gallery found at %s' % self.url)
			self.url = httpy.between(r, "class='gallery_title'><a href='", "'")[0]
		if not '/gallery/' in self.url:
			raise Exception('expected /gallery/ not found in URL')
		if not self.url.endswith('/'): self.url += '/'

	def get_album_name(self):
		album = self.url.split('/gallery/')[1]
		album = album.split('/')[0]
		album = album.split('?')[0]
		album = album.split('&')[0]
		album = album.split('#')[0]
		return album

	def get_urls(self):
		from time import sleep
		from threading import Thread
		r = self.httpy.get(self.url)
		self.result = []
		index = page = 0
		album_name = self.get_album_name()
		while True:
			for link in self.httpy.between(r, "href='http://www.imagebam.com/image/", "'"):
				link = 'http://imagebam.com/image/%s' % link
				index += 1
				# Launch thread
				while len(self.threads) >= self.max_threads:
					sleep(0.1)
				self.threads.append(None)
				t = Thread(target=self.get_image_from_page, args=(link, index))
				t.start()
			page += 1
			if 'class="pagination_link">%d</a>' % page in r:
				r = self.httpy.get('%s%d' % (self.url, page))
			else:
				break
		while len(self.threads) > 0:
			sleep(0.1)
		return self.result

	def get_image_from_page(self, page, index):
		r = self.httpy.get(page)
		if 'scale(this);" src="' in r:
			self.result.append({
				'url' : self.httpy.between(r, 'scale(this);" src="', '"')[0],
				'index' : index
			})
		self.threads.pop()
		
	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteImagebam.get_host():
			return None
		return 'http://imagebam.com/gallery/%s/' % fields[1]

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteImagebam.get_sample_url()
		s = SiteImagebam(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	SiteImagebam.test()

