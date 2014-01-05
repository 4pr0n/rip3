#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class VideoSeenive(VideoBase):

	@staticmethod
	def get_host():
		return 'seenive'

	@staticmethod
	def can_rip(url):
		return 'seenive.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://seenive.com/v/1031116119903268864'

	def rip_video(self):
		r = self.httpy.get(self.url)
		if not 'source src="' in r:
			raise Exception('could not find source src=" at ' % self.url)
		vid = self.httpy.between(r, 'source src="', '"')[0]

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoSeenive)

if __name__ == '__main__':
	VideoSeenive.test()
