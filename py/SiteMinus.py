#!/usr/bin/python

from SiteBase import SiteBase

class SiteMinus(SiteBase):

	@staticmethod
	def get_host():
		return 'minus'

	@staticmethod
	def can_rip(url):
		return 'minus.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://exogallery.minus.com/mMtlHjgWEVz9J'
		#return 'http://exogallery.minus.com/'

	def sanitize_url(self):
		if '/i/' in self.url:
			raise Exception('/i/ indicates this is a minus image, not album')
		url = self.url.replace('http://', '').replace('https://', '')
		url = url.split('?')[0]
		url = url.split('#')[0]
		url = url.split('&')[0]
		fields = url.split('minus.com/')

		if not '.minus.com' in url:
			# Guest album
			self.url = 'http://minus.com/%s' % fields[1].split('/')[0]
			return

		if ''        in fields: fields.remove('')
		if 'uploads' in fields: fields.remove('uploads')
		fields[0] = fields[0].replace('.', '')
		if len(fields) == 1:
			self.url = 'http://%s.minus.com/' % fields[0]
		else:
			self.url = 'http://%s.minus.com/%s' % (fields[0], fields[1])

	def get_album_name(self):
		url = self.url.replace('http://', '').replace('https://', '')
		if not '.minus.com' in url:
			return 'guest_%s' % url.split('minus.com/')[1]
		fields = url.split('.minus.com/')
		while '' in fields:
			fields.remove('')
		return '_'.join(fields)

	def get_urls(self):
		name = self.get_album_name()
		if '_' in name:
			# Single album download
			return self.get_urls_album(self.url)

		# Account download
		self.url = '%suploads' % self.url
		r = self.httpy.get(self.url)
		result = []
		for album in self.httpy.between(r, 'reader_id": "', '"'):
			urls = self.get_urls_album('http://%s.minus.com/m%s' % (name, album))
			result.extend(urls)
		return result

	def get_urls_album(self, album):
		from json import loads
		r = self.httpy.get(album)
		if not 'var gallerydata = {' in r:
			return []
		json = loads(self.httpy.between(r, 'var gallerydata = ', '};')[0] + '}')
		result = []
		for item in json['items']:
			name = item['name']
			imgid = item['id']
			result.append('http://i.minus.com/i%s%s' % (imgid, name[name.rfind('.'):]))
		return result

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteMinus.get_host():
			return None
		if len(fields) == 2:
			return 'http://%s.minus.com/' % fields[-1]
		else:
			return 'http://%s.minus.com/%s' % (fields[1], fields[2])

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		url = SiteMinus.get_sample_url()
		s = SiteMinus(url)
		urls = s.get_urls()
		for (i, u) in enumerate(urls):
			print i,u

		expected = 5
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		return None

if __name__ == '__main__':
	print SiteMinus.test()

