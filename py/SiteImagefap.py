#!/usr/bin/python

from SiteBase import SiteBase

class SiteImagefap(SiteBase):

	@staticmethod
	def get_host():
		return 'imagefap'

	@staticmethod
	def get_sample_url():
		return 'http://www.imagefap.com/pictures/3802288/asdf'

	@staticmethod
	def can_rip(url):
		return 'imagefap.com' in url and \
		   ('/pictures/' in url or \
		    'gid=' in url)

	@staticmethod
	def get_gid(url):
		if '/pictures/' in url:
			gid = url[url.find('/pictures/')+len('/pictures/'):]
			if '/' in gid:
				gid = gid[:gid.find('/')]
		elif 'gid=' in url:
			gid = url[url.find('gid=')+len('gid='):]
			if '&' in gid:
				gid = gid[:gid.find('&')]
		return gid

	def sanitize_url(self):
		self.url = 'http://www.imagefap.com/gallery.php?gid=%s&view=2' % SiteImagefap.get_gid(self.url) # No sanitization needed

	def get_album_name(self):
		return SiteImagefap.get_gid(self.url)

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()
		r = httpy.get(self.url)
		r = r[r.find('showMoreGalleries'):] # To ignore user icon
		links = httpy.between(r, 'border=0 src="', '"')
		result = []
		for link in links:
			link = 'http://%s' % link[link.find('.')+1:].replace('/images/thumb/', '/images/full/')
			result.append(link)
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
		return result

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) != 2 or fields[0] != SiteImagefap.get_host():
			return None
		return 'http://www.imagefap.com/gallery.php?gid=%s&view=2' % fields[1]

	@staticmethod
	def test():
		url = 'http://www.imagefap.com/pictures/3802288/asdf'
		s = SiteImagefap(url)
		urls = s.get_urls()
		expected = 10
		if len(urls) != expected:
			raise Exception('expected %d images, got %d. url: %s' % (expected, len(urls), url))

if __name__ == '__main__':
	SiteImagefap.test()
