#!/usr/bin/python

'''
	Skeleton class for site ripper
'''
from SiteBase import SiteBase

class SiteXhamster(SiteBase):

	@staticmethod
	def get_host():
		return 'xhamster'

	@staticmethod
	def can_rip(url):
		return 'xhamster.com' in url and '/photos/gallery/' in url

	@staticmethod
	def get_sample_url():
		# 109 images
		#return 'http://xhamster.com/photos/gallery/141737/big_boobed_brunette_self_shot_amateur_hottie_2.html'
		return 'http://xhamster.com/photos/gallery/1479233/sarah_from_glasgow.html'

	def sanitize_url(self):
		url = self.url
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		if '.html' in url and url[url.find('.html')-2] == '-':
			i = url.find('.html')
			url = url[:i-2] + url[i:]
		self.url = url

	def get_album_name(self):
		return self.url.split('/')[-2]

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()

		result = []
		page = 1
		r = httpy.get(self.url)
		while True:
			for chunk in httpy.between(r, "class='slideTool'", 'Related Galleries'):
				for link in httpy.between(chunk, "' src='", "'"):
					link = link.replace('_160.', '_1000.').replace('http://p2.', 'http://up.')
					result.append(link)
				break
			page += 1
			next_page = self.url.replace('.html', '-%d.html' % page)
			if next_page in r:
				r = httpy.get(next_page)
			else:
				break
		return result

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteXhamster.get_host():
			return None
		return 'http://xhamster.com/photos/gallery/%s/asdf.html' % fields[1]

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://xhamster.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = SiteXhamster.get_sample_url()
		s = SiteXhamster(url)
		urls = s.get_urls()

		expected = 10
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)
		return None

if __name__ == '__main__':
	SiteXhamster.test()
