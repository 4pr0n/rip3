#!/usr/bin/python

'''
	Skeleton class for site ripper
'''
from SiteBase import SiteBase

class SiteChansluts(SiteBase):

	@staticmethod
	def get_host():
		return 'chansluts'

	@staticmethod
	def can_rip(url):
		return 'chansluts.com' in url and '/res/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.chansluts.com/camwhores/girls/res/3405.php'

	def sanitize_url(self):
		url = self.url
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		# http://www.chansluts.com/camwhores/girls/res/3405.php
		#   0  1         2              3      4    5    6
		fields = url.split('/')
		self.url = 'http://www.chansluts.com/%s' % '/'.join(fields[3:])

	def get_album_name(self):
		fields = self.url.split('/')
		fields.remove('res')
		fields[-1] = fields[-1].replace('.php', '')
		return '-'.join(fields[3:])

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()

		r = httpy.get(self.url)
		result = []
		for post in httpy.between(r, 'daposts">', '</div> </div> </div>'):
			images = httpy.between(post, 'href="', '"')
			if len(images) > 0 and 'javascript:' not in images[0]:
				result.append('http://www.chansluts.com%s' % images[0])
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
		url = 'http://www.chansluts.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = SiteChansluts.get_sample_url()
		s = SiteChansluts(url)
		urls = s.get_urls()
		expected = 10
		if len(urls) < expected:
			raise Exception('expected at least %d images, got %d. url: %s' % (expected, len(urls), url))

if __name__ == '__main__':
	SiteChansluts.test()
