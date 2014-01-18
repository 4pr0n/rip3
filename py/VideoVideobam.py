#!/usr/bin/python

from VideoBase import VideoBase

class VideoVideobam(VideoBase):

	@staticmethod
	def get_host():
		return 'videobam'

	@staticmethod
	def can_rip(url):
		return 'videobam.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://videobam.com/tGcKD'

	def rip_video(self):
		from json import loads
		r = self.httpy.get(self.url)
		jsons = self.httpy.between(r, 'var player_config = ', ';')
		if len(jsons) == 0:
			raise Exception('no "videoMp4" found at %s' % self.url)
		json = loads(jsons[0])
		vid = json['playlist'][1]['url']

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoVideobam)

if __name__ == '__main__':
	VideoVideobam.test()
