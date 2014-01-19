#!/usr/bin/python

from VideoBase import VideoBase

class VideoVporn(VideoBase):

	@staticmethod
	def get_host():
		return 'vporn'

	@staticmethod
	def can_rip(url):
		return 'vporn.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.vporn.com/female/faye-reagan-does-the-photographer/210026/'

	def rip_video(self):
		r = self.httpy.get(self.url)
		qualities = [
			'flashvars.videoUrlHD  = "',
			'flashvars.videoUrlMedium  = "',
			'flashvars.videoUrlLow  = "'
		]
		vid = None
		for quality in qualities:
			qs = self.httpy.between(r, quality, '"')
			if len(qs) == 0 or qs[0].strip() == '':
				continue
			vid = qs[0]
			break
		if vid == None:
			raise Exception('no flashvars.videoUrl found at %s' % self.url)

		result = self.get_video_info(vid)
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoVporn)

if __name__ == '__main__':
	VideoVporn.test()
