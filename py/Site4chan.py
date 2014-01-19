#!/usr/bin/python

'''
	Skeleton class for site ripper
'''
from SiteBase import SiteBase
from json import loads

class Site4chan(SiteBase):

	@staticmethod
	def get_host():
		return '4chan'

	@staticmethod
	def get_sample_url():
		return 'http://api.4chan.org/r/res/11975234'

	@staticmethod
	def can_rip(url):
		# Expecting http[s]://[boards.]4chan.org/(board)/res/(thread)
		return '4chan.org/' in url and \
		       '/res/'      in url and \
		       len(url.split('/')) > 5

	def get_album_name(self):
		fields = self.url.split('/')
		# http://boards.4chan.org/b/res/523200202
		#   0  1         2        3  4      5
		return '%s-%s' % (fields[3], fields[5])

	def get_urls(self):
		from Httpy import Httpy
		httpy = Httpy()

		fields = self.url.split('/')
		url = 'http://api.4chan.org/%s/res/%s.json' % (fields[3], fields[5])
		try:
			r = httpy.get(url)
			json = loads(r)
			posts = json['posts']
		except Exception, e:
			raise Exception('failed to load %s: %s' % (url, str(e)))

		index = 1
		results = []
		for post in posts:
			if 'tim' not in post or 'ext' not in post:
				continue
			image = 'http://images.4chan.org/%s/src/%s%s' % (fields[3], post['tim'], post['ext'])
			result = {
				'url' : image
			}
			if 'filename' in post:
				result['saveas'] = '%03d_%s%s' % (index, post['filename'], post['ext'])
			if 'com' in post:
				result['metadata'] = post['com']
			index += 1
			results.append(result)

		# TODO archive thread to .html

		return results

	@staticmethod
	def get_url_from_album_path(album):
		# 4chan_b-34871
		# http://boards.4chan.org/b/res/34871
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != Site4chan.get_host():
			return None
		subfields = fields[1].split('-')
		return 'http://boards.4chan.org/%s/res/%s' % (subfields[0], subfields[1])

	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://boards.4chan.org/b/'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets images from a random album
		try:
			# Get first thread on /r/
			url = 'http://api.4chan.org/r/1.json'
			threads = httpy.get(url)
			json = loads(threads)
			thread = json['threads'][0]['posts'][0]
			number = thread['no']
		except Exception, e:
			raise Exception('failed to load %s: %s' % (url, str(e)))

		url = 'http://boards.4chan.org/r/res/%d' % number
		s = Site4chan(url)
		urls = s.get_urls()
		if len(urls) == 0:
			return 'expected >0 images, got %d. url: %s' % (len(urls), url)
		return None

if __name__ == '__main__':
	Site4chan.test()
