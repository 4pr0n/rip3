#!/usr/bin/python

from VideoBase import VideoBase

class VideoFapjacks(VideoBase):

	@staticmethod
	def get_host():
		return 'fapjacks'

	@staticmethod
	def can_rip(url):
		return 'fapjacks.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.fapjacks.com/video/good-looking-couple-having-sex-in-jacuzzi-Gc8JsjjNb9g.html'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vids = self.httpy.between(r, "file: '", "'")
		if len(vids) == 0:
			raise Exception('no type=video/mp4= found at %s' % self.url)
		vid = vids[0]

		result = self.get_video_info(vid)
		#result['poster'] = None # Beeg doesn't provide video splash images
		#result['no_video'] = True # Don't embed video
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoFapjacks)

if __name__ == '__main__':
	VideoFapjacks.test()
