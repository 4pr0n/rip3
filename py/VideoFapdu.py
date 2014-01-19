#!/usr/bin/python

from VideoBase import VideoBase

class VideoFapdu(VideoBase):

	@staticmethod
	def get_host():
		return 'fapdu'

	@staticmethod
	def can_rip(url):
		return 'fapdu.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://fapdu.com/x-art-sex-supermodel-2'

	def rip_video(self):
		r = self.httpy.get(self.url)
		if '"file" : "' in r:
			vids = self.httpy.between(r, '"file" : "', '"')
			vid = vids[0]
		elif 'class="watch-on" href="' in r:
			embeds = self.httpy.between(r, 'class="watch-on" href="', '"')
			embed = embeds[0]
			from VideoPornhub import VideoPornhub
			ph = VideoPornhub(embed)
			return ph.rip_video()

		result = self.get_video_info(vid)
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoFapdu)

if __name__ == '__main__':
	VideoFapdu.test()
