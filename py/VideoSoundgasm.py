#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class VideoSoundgasm(VideoBase):

	@staticmethod
	def get_host():
		return 'soundgasm'

	@staticmethod
	def can_rip(url):
		return 'soundgasm.net/' in url

	@staticmethod
	def get_sample_url():
		return 'http://soundgasm.net/u/Trinity_X/Glass'		

	def rip_video(self):
		# if not 'soundgasm.net/u/' in self.url:
		# 	raise Exception('video ripper can only rip single videos at a time. try the album ripper for user pages')
		r = self.httpy.get(self.url)
		if not 'm4a"' in r:
			raise Exception('could not find source file" at %s' % self.url)
		vid = self.httpy.between(r, 'm4a: "', '"')[0]

		result = self.get_video_info(vid)
		# result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoSoundgasm)

if __name__ == '__main__':
	VideoSoundgasm.test()
