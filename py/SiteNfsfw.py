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
		return 'http://nfsfw.com/gallery/v/HipBows/'
		#return 'http://nfsfw.com/gallery/v/dirtyberd/'
		#return 'http://nfsfw.com/gallery/v/PandaLuvs/'

	def sanitize_url(self):
		if not '/gallery/' in self.url:
			raise Exception('expected /gallery/ not found in URL')
		self.url = self.url.split('?')[0]
		self.url = self.url.split('#')[0]
		self.url = self.url.split('&')[0]
		if not self.url.endswith('/'): self.url += '/'

	def get_album_name(self):
		album = self.url.split('/')[-2]
		return SiteBase.fs_safe(album)

	def get_urls(self):
		urls = []
		albums = [self.url]
		already_got = []
		subalbum = False
		while len(albums) > 0 and len(urls) < SiteBase.MAX_IMAGES_PER_RIP:
			url = albums.pop()
			already_got.append(url)
			(new_urls, new_albums) = self.get_urls_and_albums_from_url(url, subalbum=subalbum)
			urls.extend(new_urls)
			for album in new_albums:
				if album not in already_got and album not in albums:
					albums.append(album)
			if len(urls) > SiteBase.MAX_IMAGES_PER_RIP:
				break
			subalbum = True
		return urls

	def get_urls_and_albums_from_url(self, url, subalbum=False):
		page = 1
		albums = []
		urls = []
		while True:
			next_page = '%s?g2_page=%d' % (url, page)
			r = self.httpy.get(next_page)

			# Get subalbums
			new_albums = self.get_albums_from_page(r)
			albums.extend(new_albums)
			# Get images
			new_urls = self.get_urls_from_page(r, subalbum=subalbum)
			urls.extend(new_urls)
			if len(new_urls) == 0 or len(urls) > SiteBase.MAX_IMAGES_PER_RIP:
				break
			# Next page
			page += 1
			if 'g2_page=%d' % page not in r:
				break
		return (urls, albums)

	def get_albums_from_page(self, source):
		albums = []
		for album in self.httpy.between(source, '<a href="/gallery/v/', '"'):
			if not album.endswith('/'): continue
			albums.append('http://nfsfw.com/gallery/v/%s' % album)
		return albums

	def get_urls_from_page(self, source, subalbum=False):
		result = []
		for img in self.httpy.between(source, 'img src="/gallery/d/', '"'):
			# Dirs/subdirs end with -1 or -3
			if '-2/' in img: continue

			fields = img.split('-')
			f1 = int(fields[0])
			f2 = fields[1]
			if subalbum:
				f1 -= 1
				f2 = '1%s' % f2[1:]
			else:
				f1 += 1
			result.append('http://nfsfw.com/gallery/d/%d-%s' % (f1, f2))
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

