#!/usr/bin/python

from SiteBase import SiteBase

class SiteTeenplanet(SiteBase):

	@staticmethod
	def get_host():
		return 'teenplanet'

	@staticmethod
	def can_rip(url):
		return 'teenplanet.org/' in url

	@staticmethod
	def get_sample_url():
		#return 'http://photos.teenplanet.org/atomicfrog/Dromeus/Skinny_Babe_vs_Bfs_Cock'
		#return 'http://photos.teenplanet.org/atomicfrog/Paprika/Young_and_Hot'
		return 'http://photos.teenplanet.org/atomicfrog/Amateur_Obsession/Naughty_UK_Nat'

	def sanitize_url(self):
		if not 'photos.teenplanet.org' in self.url:
			raise Exception('expected photos.teenplanet.org/ not found in URL')
		if '/page' in self.url:
			self.url = self.url[:self.url.find('/page')]
		self.url = self.url.split('?')[0]
		self.url = self.url.split('#')[0]
		self.url = self.url.split('&')[0]
		if self.url.endswith('/'): self.url = self.url[:-1]

	def get_album_name(self):
		url = self.url.replace('http://', '').replace('https://', '')
		album = '-'.join(url.split('/')[1:])
		return SiteBase.fs_safe(album)

	def get_urls(self):
		from time import sleep
		from threading import Thread

		try:
			r = self.httpy.get(self.url)
		except:
			return []

		index = 0
		page = 1
		self.result = []
		while True:
			chunks = self.httpy.between(r, '<div class="thumb">', '</div>')
			if len(chunks) == 0:
				break

			for chunk in chunks:
				if not 'a href="' in chunk: continue
				link = 'http://photos.teenplanet.org%s' % self.httpy.between(chunk, 'a href="', '"')[0]
				while len(self.threads) >= self.max_threads:
					sleep(0.1)
				self.threads.append(None)
				index += 1
				t = Thread(target=self.get_link_from_page, args=(link, index,))
				t.start()
				if len(self.result) + len(self.threads) > SiteBase.MAX_IMAGES_PER_RIP:
					break

			# Next page
			page += 1
			if '/page%d">' % page not in r:
				break
			try:
				r = self.httpy.get('%s/page%d' % (self.url, page))
			except:
				break

		while len(self.threads) > 0:
			sleep(0.1)
		return self.result

	def get_link_from_page(self, link, index):
		try:
			r = self.httpy.get(link)
			if '<div id="full-size">' in r:
				chunk = self.httpy.between(r, '<div id="full-size">', '</div>')[0]
				url = self.httpy.between(chunk, 'href="', '"')[0]
				url = 'http://photos.teenplanet.org%s' % url.replace(' ', '%20')
				self.result.append({
					'url' : url,
					'index' : index
				})
		except:
			pass
		self.threads.pop()

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteTeenplanet.get_host():
			return None
		return 'http://photos.teenplanet.org/%s' % '_'.join(fields[1:]).replace('-', '/')

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteTeenplanet.get_sample_url()
		s = SiteTeenplanet(url)
		print url
		print s.get_album_name()
		print SiteTeenplanet.get_url_from_album_path(s.path)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	print SiteTeenplanet.test()
