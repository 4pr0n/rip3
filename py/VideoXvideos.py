#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class VideoXvideos(VideoBase):

	@staticmethod
	def get_host():
		return 'xvideos'

	@staticmethod
	def can_rip(url):
		return 'xvideos.com/video' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.xvideos.com/video2722581/stella_luzz_my_dorm_life'

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
		return VideoBase.test_ripper(VideoXvideos)

if __name__ == '__main__':
	VideoXvideos.test()
