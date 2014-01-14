#!/usr/bin/python

from SiteBase import SiteBase

class SiteInstagram(SiteBase):

	@staticmethod
	def get_host():
		return 'instagram'

	@staticmethod
	def can_rip(url):
		return 'instagram.com' in url

	@staticmethod
	def get_sample_url():
		return 'http://instagram.com/mileys_lesbian'

	def sanitize_url(self):
		if 'instagram.com/p/' in self.url:
			raise Exception('cannot rip single instagram pages, must be user pages')
		user = self.url.split('instagram.com/')[1]
		user = user.split('/')[0]
		user = user.split('#')[0]
		self.url = 'http://instagram.com/%s' % user

	def get_album_name(self):
		user = self.url.split('instagram.com/')[1]
		user = user.split('/')[0]
		user = user.split('#')[0]
		return user

	def get_urls(self):
		from json import loads
		from time import sleep
		url = self.url.replace('instagram.com/', 'statigr.am/')
		r = self.httpy.get(url)
		if not 'id="user_public" value="' in r:
			raise Exception('unable to find user_id at %s' % self.url)
		userid  = self.httpy.between(r, 'id="user_public" value="', '"')[0]

		baseurl = 'http://statigr.am/controller_nl.php?action=getPhotoUserPublic&user_id=%s' % userid
		params  = ''
		max_id  = ''
		result  = []
		while True:
			r = self.httpy.get('%s%s' % (baseurl, params))
			json = loads(r)
			datas = json.get('data', [])
			if len(datas) == 0:
				break
			for data in datas:
				if 'id' in data:
					max_id = '%s_%s' % (data['id'], userid)

				if 'videos' in data:
					result.append(data['videos']['standard_resolution']['url'])
				elif 'images' in data:
					result.append(data['images']['standard_resolution']['url'])
			if max_id == '':
				if not 'next_max_id' in json.get('pagination', []):
					break
				max_id = json['pagination']['next_max_id']
			params = '&max_id=%s' % max_id
			sleep(2)
		return result

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteInstagram.get_host():
			return None
		return 'http://instagram.com/%s' % fields[-1]

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		# Check ripper gets all images in an album
		url = SiteInstagram.get_sample_url()
		s = SiteInstagram(url)
		urls = s.get_urls()
		for i,u in enumerate(urls):
			print i,u
		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)
		return None

if __name__ == '__main__':
	print SiteInstagram.test()
