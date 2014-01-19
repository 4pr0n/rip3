#!/usr/bin/python

from VideoBase import VideoBase

class VideoSetsdb(VideoBase):

	@staticmethod
	def get_host():
		return 'setsdb'

	@staticmethod
	def can_rip(url):
		return 'setsdb.org/' in url

	@staticmethod
	def get_sample_url():
		#return 'http://setsdb.org/tori-torrid-love-2/'
		return 'http://setsdb.org/bree-celeste-colours-of-passion/'

	def rip_video(self):
		r = self.httpy.get(self.url)
		iframes = self.httpy.between(r, '<iframe src="', '"')
		if len(iframes) == 0:
			raise Exception('expected iframe src= found at %s' % self.url)
		iframe = iframes[0].replace('&#038;', '&')
		r = self.httpy.get(iframe)
		hds = ['amp;url720=', 'amp;url=480', 'amp;url=360', 'amp;url=240']
		vid = None
		for hd in hds:
			if hd in r:
				vid = self.httpy.between(r, hd, '&amp;')[0]
				break
		if vid == None:
			raise Exception('expected url###= not found at %s' % iframe)

		result = self.get_video_info(vid)
		#result['poster'] = None # Beeg doesn't provide video splash images
		#result['no_video'] = True # Don't embed video
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoSetsdb)

if __name__ == '__main__':
	VideoSetsdb.test()
