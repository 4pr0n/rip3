#!/usr/bin/python

from VideoBase import VideoBase

class VideoXtube(VideoBase):

	@staticmethod
	def get_host():
		return 'xtube'

	@staticmethod
	def can_rip(url):
		return 'xtube.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.xtube.com/watch.php?v=BHMDS-S484-'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, 'videoMp4 = "', '"')
		if len(vids) == 0:
			raise Exception('no "videoMp4" found at %s' % self.url)
		vid = vids[0].replace('\\/', '/')

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		result['no_video'] = True # Don't embed video
		result['no_redirect'] = True # Can't redirect to video, auth required
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoXtube)

if __name__ == '__main__':
	VideoXtube.test()
