#!/usr/bin/python

from VideoBase import VideoBase

class VideoVine(VideoBase):

	@staticmethod
	def get_host():
		return 'vine'

	@staticmethod
	def can_rip(url):
		return 'vine.co/v/' in url

	@staticmethod
	def get_sample_url():
		return 'https://vine.co/v/hLUEg75UttT'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, 'source src="', '"')
		if len(vids) == 0:
			raise Exception('no "videoMp4" found at %s' % self.url)
		vid = vids[0]

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoVine)

if __name__ == '__main__':
	VideoVine.test()
