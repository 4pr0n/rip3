#!/usr/bin/python

from VideoBase import VideoBase

class VideoMobypicture(VideoBase):

	@staticmethod
	def get_host():
		return 'mobypicture'

	@staticmethod
	def can_rip(url):
		return 'mobypicture.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.mobypicture.com/user/VerboEros/view/14190094'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, 'file: "', '"')
		if len(vids) == 0:
			raise Exception('no mp4File= found at %s' % self.url)
		vid = vids[0]

		result = self.get_video_info(vid)
		#result['poster'] = None # Beeg doesn't provide video splash images
		#result['no_video'] = True # Don't embed video
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoMobypicture)

if __name__ == '__main__':
	VideoMobypicture.test()
