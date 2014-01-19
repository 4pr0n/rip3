#!/usr/bin/python

from VideoBase import VideoBase

class VideoKinkylicious(VideoBase):

	@staticmethod
	def get_host():
		return 'kinkylicious'

	@staticmethod
	def can_rip(url):
		return 'kinkylicious.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.kinkylicious.com/video/1146/skinny-girl-fucked-doggystyle.html'

	def rip_video(self):
		r = self.httpy.get(self.url)

		if 'var video_id = "' in r:
			vid = self.httpy.between(r, 'var video_id = "', '"')[0]
		elif "so.addVariable('videoid','" in r:
			vid = self.httpy.between(r, "so.addVariable('videoid','", "'")[0]
		else:
			raise Exception('no videoid found at %s' % self.url)

		vid = 'http://kinkylicious.com/vdata/%s.flv' % vid

		result = self.get_video_info(vid)
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoKinkylicious)

if __name__ == '__main__':
	VideoKinkylicious.test()
