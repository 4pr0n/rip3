#!/usr/bin/python

from VideoBase import VideoBase

from json import loads

class VideoVimeo(VideoBase):

	@staticmethod
	def get_host():
		return 'vimeo'

	@staticmethod
	def can_rip(url):
		return 'vimeo.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://vimeo.com/17135848'

	def rip_video(self):
		r = self.httpy.get(self.url)

		# Get config
		if not 'data-config-url="' in r:
			raise Exception('no data-config-url" found at %s' % self.url)
		config = self.httpy.between(r, 'data-config-url="', '"')[0]
		config = config.replace('&amp;', '&')

		r = self.httpy.get(config)
		json = loads(r)
		formats = json['request']['files']['h264']
		for ideal in ['hd', 'sd', 'mobile']:
			if ideal in formats:
				break

		if not ideal in formats:
			raise Exception('could not find appropriate video format at %s' % self.url)

		vid = formats[ideal]['url']

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()
		try:
			r = httpy.get('http://www.vimeo.com/')
			if len(r.strip()) == 0:
				raise Exception('empty response from vimeo.com')
		except Exception, e:
			raise e
		return VideoBase.test_ripper(VideoVimeo)

if __name__ == '__main__':
	VideoVimeo.test()
