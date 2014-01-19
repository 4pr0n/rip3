#!/usr/bin/python

from VideoBase import VideoBase

class VideoSpankwire(VideoBase):

	@staticmethod
	def get_host():
		return 'spankwire'

	@staticmethod
	def can_rip(url):
		return 'spankwire.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.spankwire.com/Two-real-hot-college-girls-play-with-perfect-boobs/video1181681/'

	def rip_video(self):
		r = self.httpy.get(self.url)
		vid = None
		for qual in ['720', '480', '320', '240', '180']:
			qs = self.httpy.between(r, 'flashvars.quality_%sp = "' % qual, '"')
			if len(qs) == 0 or qs[0] == '':
				continue
			vid = qs[0]

		if vid == None:
			raise Exception('no flashvars.quality_### found at %s' % self.url)
		from urllib import unquote
		vid = unquote(vid)

		result = self.get_video_info(vid)
		#result['poster'] = None # Beeg doesn't provide video splash images
		#result['no_video'] = True # Don't embed video
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoSpankwire)

if __name__ == '__main__':
	VideoSpankwire.test()
