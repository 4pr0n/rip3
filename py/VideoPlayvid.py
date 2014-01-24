#!/usr/bin/python

from VideoBase import VideoBase

class VideoPlayvid(VideoBase):

	@staticmethod
	def get_host():
		return 'playvid'

	@staticmethod
	def can_rip(url):
		return 'playvid.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.playvid.com/watch?v=L9VYsrrnIyX'

	def rip_video(self):
		r = self.httpy.get(self.url)
		chunks = self.httpy.between(r, 'video_urls%5D%5B', '&')
		if len(chunks) == 0:
			raise Exception('no video_urls found at %s' % self.url)
		vid = None
		for chunk in sorted(chunks, reverse=True):
			if len(chunk) < 10: continue
			vid = chunk[chunk.find('=')+1:]
		if vid == None:
			raise Exception('could not find video_url at %s' % self.url)
		from urllib import unquote
		vid = unquote(vid)

		result = self.get_video_info(vid)
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoPlayvid)

if __name__ == '__main__':
	VideoPlayvid.test()
