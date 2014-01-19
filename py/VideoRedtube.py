#!/usr/bin/python

from VideoBase import VideoBase

class VideoRedtube(VideoBase):

	@staticmethod
	def get_host():
		return 'redtube'

	@staticmethod
	def can_rip(url):
		return 'redtube.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.redtube.com/25814'

	def rip_video(self):
		r = self.httpy.get(self.url)
		if '&mp4_url=' in r:
			vid = self.httpy.between(r, '&mp4_url=', '&')[0]
		elif '&flv_url=' in r:
			vid = self.httpy.between(r, '&flv_url=', '&')[0]
		else:
			raise Exception('no flv/mp4_url= found at %s' % self.url)
		from urllib import unquote
		vid = unquote(vid)

		result = self.get_video_info(vid)
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoRedtube)

if __name__ == '__main__':
	VideoRedtube.test()
