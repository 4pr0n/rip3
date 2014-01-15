#!/usr/bin/python

from SiteBase import SiteBase

class SiteSeenive(SiteBase):

	@staticmethod
	def get_host():
		return 'seenive'

	@staticmethod
	def can_rip(url):
		return 'seenive.com/' in url

	@staticmethod
	def get_sample_url():
		#return 'http://seenive.com/u/911429150038953984'
		return 'http://seenive.com/u/934657356531380224'

	def sanitize_url(self):
		if not '/u/' in self.url:
			raise Exception('expected /u/ not found in URL')
		self.url = 'http://seenive.com/u/%s' % self.url.split('/u/')[1]
		self.url = self.url.split('?')[0]
		self.url = self.url.split('#')[0]
		self.url = self.url.split('&')[0]
		if self.url.endswith('/'): self.url = self.url[:-1]

	def get_album_name(self):
		album = self.url.split('/')[-1]
		return SiteBase.fs_safe(album)

	def get_urls(self):
		from time import sleep
		from threading import Thread

		try:
			r = self.httpy.get(self.url)
		except:
			return []
		self.result = []
		while True:
			links = self.httpy.between(r, "updateVideo('", "'")
			if len(links) == 0:
				break
			for (index, link) in enumerate(links):
				link = 'http://seenive.com/v/%s' % link
				while len(self.threads) >= self.max_threads:
					sleep(0.1)
				self.threads.append(None)
				t = Thread(target=self.get_link_from_page, args=(link, index,))
				t.start()
				if len(self.result) + len(self.threads) > SiteBase.MAX_IMAGES_PER_RIP:
					break
			if len(self.result) + len(self.threads) > SiteBase.MAX_IMAGES_PER_RIP:
				break
			# Next page
			if 'postFeed.lastPostId = "' not in r:
				break
			prev_id = self.httpy.between(r, 'postFeed.lastPostId = "', '"')[0]
			try:
				r = self.httpy.get('%s?prevId=%s' % (self.url, prev_id))
			except:
				break

		while len(self.threads) > 0:
			sleep(0.1)
		return self.result

	def get_link_from_page(self, link, index):
		try:
			r = self.httpy.get(link)
			src = self.httpy.between(r, '<source src="', '"')[0]
			self.result.append(src)
		except:
			pass
		self.threads.pop()
		
	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteSeenive.get_host():
			return None
		return 'http://seenive.com/u/%s' % fields[-1]

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteSeenive.get_sample_url()
		s = SiteSeenive(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	SiteSeenive.test()
