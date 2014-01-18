#!/usr/bin/python

from VideoBase import VideoBase

class VideoYouporn(VideoBase):

	@staticmethod
	def get_host():
		return 'youporn'

	@staticmethod
	def can_rip(url):
		return 'youporn.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.youporn.com/watch/8966022/x-art-best-lesbian-threesome-ever-with-caprice-and-eufrat/'

	def rip_video(self):
		r = self.httpy.get(self.url)
		chunks = self.httpy.between(r, '<video ', '</video>')
		if len(chunks) == 0:
			raise Exception('no "video" tag found at %s' % self.url)
		vid = self.httpy.between(chunks[0], 'src="', '"')[0]
		vid = vid.replace('&amp;', '&')

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoYouporn)

if __name__ == '__main__':
	VideoYouporn.test()
