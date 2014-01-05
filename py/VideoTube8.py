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

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoTube8)

if __name__ == '__main__':
	VideoTube8.test()
