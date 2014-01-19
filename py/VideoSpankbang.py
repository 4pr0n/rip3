#!/usr/bin/python

from VideoBase import VideoBase

class VideoSpankbang(VideoBase):

	@staticmethod
	def get_host():
		return 'spankbang'

	@staticmethod
	def can_rip(url):
		return 'spankbang.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://spankbang.com/1tyt/video/joymii+josephine+'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, 'file: "', '"')
		if len(vids) == 0:
			raise Exception('no file: found at %s' % self.url)
		vid = 'http://spankbang.com%s' % vids[0]

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		result['no_video'] = True # Don't embed video
		result['no_redirect'] = True # Don't embed video
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoSpankbang)

if __name__ == '__main__':
	VideoSpankbang.test()
