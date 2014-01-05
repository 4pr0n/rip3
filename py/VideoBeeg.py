#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class VideoBeeg(VideoBase):

	@staticmethod
	def get_host():
		return 'beeg'

	@staticmethod
	def can_rip(url):
		return 'beeg.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://beeg.com/4554321'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, "'file': '", "'")
		if len(vids) == 0:
			raise Exception('no mp4File= found at %s' % self.url)
		vid = vids[0]

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result
	
	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoBeeg)

if __name__ == '__main__':
	VideoBeeg.test()
