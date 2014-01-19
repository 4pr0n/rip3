#!/usr/bin/python

from VideoBase import VideoBase

class VideoPornably(VideoBase):

	@staticmethod
	def get_host():
		return 'pornably'

	@staticmethod
	def can_rip(url):
		return 'pornably.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.pornably.com/video/1387'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, 'source type="video/mp4" src="', '"')
		if len(vids) == 0:
			raise Exception('no source type video/mp4 found at %s' % self.url)
		vid = vids[0]

		result = self.get_video_info(vid)
		#result['poster'] = None # Beeg doesn't provide video splash images
		#result['no_video'] = True # Don't embed video
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoPornably)

if __name__ == '__main__':
	VideoPornably.test()
