#!/usr/bin/python

from SiteBase import SiteBase

from json import loads
from time import sleep

class SiteImgur(SiteBase):

	@staticmethod
	def get_host():
		return 'imgur'

	@staticmethod
	def get_sample_url():
		#return 'http://imgur.com/a/RdXNa'
		return 'http://arseredraw.imgur.com/'

	@staticmethod
	def can_rip(url):
		# Album
		if 'imgur.com/a/' in url:
			return True

		# Subreddit
		elif 'imgur.com/r/' in url:
			return True

		# User account
		elif '.imgur.com' in url and \
		     '/www.imgur.com' not in url and \
		     '/m.imgur.com'   not in url and \
		     '/i.imgur.com'   not in url:
			return True

		return False

	def sanitize_url(self):
		url = self.url
		url = 'http://%s' % url.replace('http://', '').replace('https://', '')
		url = url.replace('/m.imgur.com/', '/imgur.com/')
		url = url.replace('/www.imgur.com/', '/imgur.com/')
		url = url.split('#')[0]
		url = url.split('?')[0]
		url = url.split('&')[0]
		if not url.endswith('/'):
			url += '/'
		if 'imgur.com/a/' in url:
			url = 'http://imgur.com/a/%s' % url.split('imgur.com/a/')[1].split('/')[0]
		if 'imgur.com/r/' in url:
			fields = url.split('/')
			url = 'http://imgur.com/r/%s' % '/'.join(fields[4:])
		self.url = url

	def get_album_name(self):
		# Album
		if 'imgur.com/a/' in self.url:
			# http://imgur.com/a/album
			return self.url.split('/')[-1]

		# Subreddit
		if 'imgur.com/r/' in self.url:
			# http://imgur.com/r/RealGirls
			# http://imgur.com/r/RealGirls/new
			# http://imgur.com/r/RealGirls/top
			# http://imgur.com/r/RealGirls/top/[week/month/year/all]
			#   0  1     2     3    4       5            6
			fields = self.url.split('/')
			while '' in fields: fields.remove('')
			if len(fields) == 6 and fields[5] == 'top':
				fields.append('month') # imgur's default
			return 'r_%s' % '_'.join(fields[4:])

		# User account
		if '.imgur.com' in self.url:
			# http://user.imgur.com[/album]
			nohttp = self.url.split('//')[1]
			user = nohttp.split('.')[0]
			if nohttp.endswith('/all'):
				return 'user_%s_all' % user
			else:
				return 'user_%s' % user

	def get_urls(self):
		if 'imgur.com/a/' in self.url:
			return self.get_urls_album(self.url)
		if 'imgur.com/r/' in self.url:
			return self.get_urls_subreddit()
		if '.imgur.com' in self.url:
			return self.get_urls_user_albums()

	@staticmethod
	def get_urls_album(url):
		'''
			Requires URL in the format: http://imgur.com/a/[albumid]
		'''
		from Httpy import Httpy
		httpy = Httpy()

		try:
			r = httpy.get('http://api.imgur.com/2/album/%s.json' % url.split('/')[-1])
			json = loads(r)
			if 'error' in json:
				# Error, fall back to noscript method
				raise Exception(error)
		except Exception, e:
			# Got exception, fall back to noscript method
			return SiteImgur.get_urls_album_noscript(url)

		# TODO album metadata for json['title'] json['description']

		result = []
		for image in json['album']['images']:
			title = image['image'].get('title', '')
			caption = image['image'].get('caption', '')
			url = image['links']['original']
			result.append({
				'url' : url,
				'saveas' : url[url.rfind('/')+1:],
				'metadata' : '%s%s' % (title, caption)
			})
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
		return result

	@staticmethod
	def get_urls_album_noscript(url):
		'''
			Requires URL in the format: http://imgur.com/a/[albumid]
		'''
		from Httpy import Httpy
		httpy = Httpy()
		r = httpy.get('%s/noscript' % url)
		result = []
		for link in httpy.between(r, 'img src="//i.', '"'):
			link = 'http://i.%s' % link
			try:
				link = self.get_highest_res(link)
			except Exception, e:
				# Image is gone.
				# Add it anyway so RipManager will mark the image as 'errored'
				pass
			result.append({
				'url' : link,
				'saveas' : link[link.rfind('/')+1:]
			})
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
		return result

	def get_urls_subreddit(self):
		from Httpy import Httpy
		httpy = Httpy()

		page = 0
		result = []
		while True:
			r = httpy.get('%s/page/%d' % (self.url, page))
			links = httpy.between(r, ' src="//i.', '"')
			if len(links) == 0:
				# Hit end of pages
				return result
			for link in links:
				if link in result:
					# Pages started repeating
					return result
				link = self.get_highest_res(link)
				result.append(link)
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
			page += 1

	def get_urls_user_albums(self):
		if self.url.endswith('/all'):
			# Images, not albums
			return self.get_urls_user_images()

		from Httpy import Httpy
		httpy = Httpy()

		user = self.url.split('//')[1].split('.')[0]
		r = httpy.get(self.url)
		result = []
		for (index, cover) in enumerate(httpy.between(r, '<div class="cover">', '</div>')):
			if not '<a href="' in cover: continue
			album = httpy.between(cover, '<a href="', '"')[0]
			if album.startswith('//'):
				album = 'http:%s' % album
			albumid = album.split('/')[4]
			album = 'http://imgur.com/a/%s' % albumid
			for image in self.get_urls_album(album):
				# Tack this album's index/albumid to image
				image['saveas'] = '%03d_%s_%s' % (index + 1, albumid, image['saveas'])
				result.append(image)
			sleep(2)
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
		return result

	def get_urls_user_images(self):
		from Httpy import Httpy
		httpy = Httpy()

		result = []
		url = self.url.replace('/all', '')
		page = total = index = 0
		while True:
			page += 1
			next_page = '%s/ajax/images?sort=0&order=1&album=0&page=%d&perPage=60' % (url, page)
			r = httpy.get(next_page)
			json = loads(r)
			data = json['data']
			if total == 0 and 'count' in data:
				total = data['count']
			# TODO report progress
			for image in data['images']:
				result.append('http://i.imgur.com/%s%s' % (image['hash'], image['ext']))
			if index >= total:
				break
			if len(result) > SiteBase.MAX_IMAGES_PER_RIP:
				break
			sleep(1)
		return result

	@staticmethod
	def get_highest_res(url):
		'''
			Checks if URL is not highest-res version
			Gets highest-res version
			Args:
				url: The imgur URL
			Returns:
				URL to highest-res version of image
		'''
		if not 'h.' in url:
			return url
		temp = url.replace('h.', '.')
		m = self.httpy.get_meta(temp)
		if 'Content-Length' in m and m['Content-Length'] == '503':
			raise Exception(temp)
		if 'Content-Type' in m and 'image' in m['Content-Type'].lower():
			return temp
		else:
			return url

	@staticmethod
	def test():
		'''
			Test that ripper is working as expected.
			Raise exception if necessary.
		'''
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://imgur.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		#url = 'http://markedone911.imgur.com/'
		#url = 'http://imgur.com/r/nsfw_oc/top/all'
		url = SiteImgur.get_sample_url()
		s = SiteImgur(url)
		urls = s.get_urls()
		for (i,u) in enumerate(urls):
			print i, u
		expected = 4
		if len(urls) < expected:
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)
		return None

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if fields[0] != SiteImgur.get_host():
			return None
		if len(fields) == 2:
			# Album
			return 'http://imgur.com/a/%s' % fields[1]
		elif fields[1] == 'r':
			# Subreddit
			return 'http://imgur.com/r/%s' % '/'.join(fields[1:])
		elif fields[1] == 'user':
			if len(fields) == 4:
				return 'http://%s.imgur.com/%s' % (fields[2], fields[3])
			else:
				return 'http://%s.imgur.com/' % fields[2]

if __name__ == '__main__':
	SiteImgur.test()
	
