#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class _SampleVideo(VideoBase):

	@staticmethod
	def get_host():
		return 'hostname'

	@staticmethod
	def can_rip(url):
		return 'hostname.com/movies' in url

	@staticmethod
	def get_sample_url():
		return 'http://hostname.com/movies/asdf'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, 'mp4File=', '"')
		if len(vids) == 0:
			raise Exception('no mp4File= found at %s' % self.url)
		vid = unquote(vids[0])

		# Get info, return it
		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(_SampleVideo)

if __name__ == '__main__':
	_SampleVideo.test()
