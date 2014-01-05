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
		meta = self.httpy.get_meta(vid)
		filesize = meta.get('Content-Length', 0)
		filetype = meta.get('Content-Type', 'unknown')
		if not filetype.startswith('video/'):
			raise Exception('content-type (%s) not "video/" at %s' % (filetype, vid))
		else:
			filetype = filetype.replace('video/', '').replace('x-', '')
		return (vid, filesize, filetype)

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		# Check that we can hit the host
		url = 'http://www.vimeo.com'
		r = httpy.get(url)
		if len(r) == 0:
			raise Exception('unable to get content at %s' % url)

		# Try to rip the sample video
		url = VideoVimeo.get_sample_url()
		v = VideoVimeo(url)
		(url, filesize, filetype) = v.rip_video()

		# Assert we got the video
		if filesize == 0 or filetype == 'unknown':
			return 'unexpected filesize (%s) or filetype (%s) at %s' % (filesize, filetype, url)
		return None

if __name__ == '__main__':
	VideoVimeo.test()
