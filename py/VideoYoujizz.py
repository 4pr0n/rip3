#!/usr/bin/python

from VideoBase import VideoBase

class VideoYoujizz(VideoBase):

	@staticmethod
	def get_host():
		return 'youjizz'

	@staticmethod
	def can_rip(url):
		return 'youjizz.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.youjizz.com/videos/kasia-blue-dildo-203876.html'

	def rip_video(self):
		url = self.url
		url = url.split('?')[0]
		url = url.split('#')[0]
		vidid = url.split('.html')[0].split('-')[-1]
		url = 'http://www.youjizz.com/videos/embed/%s' % vidid
		r = self.httpy.get(url)
		vids = self.httpy.between(r, 'encodeURIComponent("', '"')
		if len(vids) == 0:
			raise Exception('no "encodeURIComponent" found at %s' % url)
		vid = vids[0].replace('\\/', '/')

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		result['no_video'] = True # Don't embed video
		result['no_redirect'] = True # Can't redirect to video, auth required
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoYoujizz)

if __name__ == '__main__':
	VideoYoujizz.test()
