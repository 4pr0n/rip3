#!/usr/bin/python

from VideoBase import VideoBase

from AES import AES
from urllib import unquote

class VideoTube8(VideoBase):

	@staticmethod
	def get_host():
		return 'tube8'

	@staticmethod
	def can_rip(url):
		return 'tube8.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.tube8.com/latina/sensi-pearl-devon-lee-fucking-the-babysitter/2305011/'

	def rip_video(self):
		r = self.httpy.get(self.url)

		if 'video_title":"' not in r:
			raise Exception('no video_title":" found at %s' % self.url)
		title = self.httpy.between(r, 'video_title":"', '"')[0]
		title = title.replace('+', ' ')

		if 'video_url":"' not in r:
			raise Exception('no video_url":" found at %s' % self.url)
		quality = self.httpy.between(r, 'video_url":"', '"')[0]
		quality = unquote(quality)

		vid = AES.decrypt(quality, title, 256)

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
		url = 'http://www.tube8.com'
		r = httpy.get(url)
		if len(r) == 0:
			raise Exception('unable to get content at %s' % url)

		# Try to rip the sample video
		url = VideoTube8.get_sample_url()
		v = VideoTube8(url)
		(url, filesize, filetype) = v.rip_video()

		# Assert we got the video
		if filesize == 0 or filetype == 'unknown':
			return 'unexpected filesize (%s) or filetype (%s) at %s' % (filesize, filetype, url)
		return None

if __name__ == '__main__':
	VideoTube8.test()
