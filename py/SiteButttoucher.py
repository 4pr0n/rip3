#!/usr/bin/python

'''
	Skeleton class for site ripper
'''
from SiteBase import SiteBase

class SiteButttoucher(SiteBase):

	@staticmethod
	def get_host():
		return 'butttoucher'

	@staticmethod
	def get_sample_url():
		return 'http://www.butttoucher.com/users/pinkiepie3'

	@staticmethod
	def can_rip(url):
		return 'butttoucher.com' in url and '/users/' in url

	def sanitize_url(self):
		if '#' in self.url: self.url = self.url[:self.url.find('#')]
		if '?' in self.url: self.url = self.url[:self.url.find('?')]

	def get_album_name(self):
		fields = self.url.split('/')
		while '' in fields:
			fields.remove('')
		return fields[-1]

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()

		r = httpy.get(self.url)
		result = []
		for link in httpy.between(r, 'src="', '"'):
			if not 'http://' in link: continue
			if not 'imgur.com' in link: continue
			doti = link.rfind('.')-1
			if link[doti] == 'm':
				link = link.replace(link[doti:], link[doti+1:])
			result.append(link)
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
		return result

	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://butttoucher.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = 'http://www.butttoucher.com/users/pinkiepie3'
		s = SiteButttoucher(url)
		urls = s.get_urls()
		expected = 5
		if len(urls) < expected:
			raise Exception('expected at least %d images, got %d. url: %s' % (expected, len(urls), url))

if __name__ == '__main__':
	SiteButttoucher.test()
