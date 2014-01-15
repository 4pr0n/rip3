#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class VideoXnxx(VideoBase):

	@staticmethod
	def get_host():
		return 'xnxx'

	@staticmethod
	def can_rip(url):
		return 'xnxx.com/video' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.xnxx.com/video6089958/gorgeous_brunette_pornstar_babe_megan_salinas_doggy_fucked'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, 'flv_url=', '&amp;')
		if len(vids) == 0:
			raise Exception('no flv_url= found at %s' % self.url)
		vid = unquote(vids[0])

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoXnxx)

if __name__ == '__main__':
	print VideoXnxx.test()
