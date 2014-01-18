#!/usr/bin/python

from VideoBase import VideoBase

class VideoVidearn(VideoBase):

	@staticmethod
	def get_host():
		return 'xtube'

	@staticmethod
	def can_rip(url):
		return 'videarn.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://videarn.com/amateur-teen/15387-37018574355.html'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, 'file: "', '"')
		if len(vids) == 0:
			raise Exception('no "file:" found at %s' % self.url)
		vid = vids[0].replace('\\/', '/')

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoVidearn)

if __name__ == '__main__':
	VideoVidearn.test()
