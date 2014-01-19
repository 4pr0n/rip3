#!/usr/bin/python

from VideoBase import VideoBase

class VideoSexykarma(VideoBase):

	@staticmethod
	def get_host():
		return 'sexykarma'

	@staticmethod
	def can_rip(url):
		return 'sexykarma.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.sexykarma.com/gonewild/video/stretching-my-tight-asshole-8JfO8lcfzHP.html'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, "playlist = [ { url: escape('", "'")
		if len(vids) == 0:
			raise Exception('no mp4File= found at %s' % self.url)
		vid = vids[0]

		result = self.get_video_info(vid)
		#result['poster'] = None # Beeg doesn't provide video splash images
		#result['no_video'] = True # Don't embed video
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoSexykarma)

if __name__ == '__main__':
	VideoSexykarma.test()
