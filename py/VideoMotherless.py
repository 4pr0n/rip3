#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class VideoMotherless(VideoBase):

	@staticmethod
	def get_host():
		return 'motherless'

	@staticmethod
	def can_rip(url):
		return 'motherless.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://motherless.com/FF6D765'

	def rip_video(self):
		r = self.httpy.get(self.url)
		if not "__fileurl = '" in r:
			raise Exception('could not find __fileurl= at ' % self.url)
		vid = self.httpy.between(r, "__fileurl = '", "'")[0]

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoMotherless)

if __name__ == '__main__':
	VideoMotherless.test()
