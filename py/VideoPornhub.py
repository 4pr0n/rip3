#!/usr/bin/python

from VideoBase import VideoBase

from AES import AES
from urllib import unquote

class VideoPornhub(VideoBase):

	@staticmethod
	def get_host():
		return 'pornhub'

	@staticmethod
	def can_rip(url):
		return 'pornhub.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.pornhub.com/view_video.php?viewkey=387635205'

	def rip_video(self):
		r = self.httpy.get(self.url)

		if 'video_title":"' not in r:
			raise Exception('no video_title":" found at %s' % self.url)
		title = self.httpy.between(r, 'video_title":"', '"')[0]
		title = title.replace('+', ' ')

		if '0p":"' not in r:
			raise Exception('no 0p":" found at %s' % self.url)
		quality = self.httpy.between(r, '0p":"', '"')[0]
		quality = unquote(quality)

		vid = AES.decrypt(quality, title, 256)

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoPornhub)

if __name__ == '__main__':
	VideoPornhub.test()
