#!/usr/bin/python

'''
	Skeleton class for site ripper
'''
from SiteBase import SiteBase
from json import loads

class Site4chan(SiteBase):

	@staticmethod
	def get_host():
		'''
			Returns name of site, no TLD (.com, .net) required
		'''
		return '4chan'

	@staticmethod
	def can_rip(url):
		'''
			Checks if this ripper can rip a URL.
		'''
		# Expecting http[s]://[boards.]4chan.org/(board)/res/(thread)
		return '4chan.org/' in url and \
		       '/res/'      in url and \
		       len(url.split('/')) > 5

	def get_album_name(self):
		'''
			Returns unique album name (unique to this class' host name)
		'''
		fields = self.url.split('/')
		# http://boards.4chan.org/b/res/523200202
		#   0  1         2        3  4      5
		return '%s-%s' % (fields[3], fields[5])

	def get_urls(self):
		'''
			Returns list of URLs from album. Does not download them.
		'''
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
		url = 'http://api.4chan.org/r/res/11975234'
		s = Site4chan(url)
		urls = s.get_urls()
		if len(urls) == 0:
			raise Exception('expected >0 images, got %d. url: %s' % (len(urls), url))
		print urls

if __name__ == '__main__':
	Site4chan.test()
