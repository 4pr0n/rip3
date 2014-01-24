#!/usr/bin/python

from VideoBase import VideoBase

class VideoCollegehumor(VideoBase):

	@staticmethod
	def get_host():
		return 'collegehumor'

	@staticmethod
	def can_rip(url):
		return 'collegehumor.com/video/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.collegehumor.com/video/5767906/the-tetris-god'

	def rip_video(self):
		vidid = self.url[self.url.find('/video/')+len('/video/'):]
		vidid = vidid.split('/')[0]
		url = 'http://www.collegehumor.com/moogaloop/video/%s.json' % vidid
		r = self.httpy.get(url)
		from json import loads
		json = loads(r)
		if not 'video' in json or not 'mp4' in json['video']:
			raise Exception('could not find video.mp4 at %s' % url)
		mp4 = json['video']['mp4']
		if 'high_quality' in mp4:
			vid = mp4['high_quality']
		elif 'low_quality' in mp4:
			vid = mp4['low_quality']
		else:
			raise Exception('could not find high/low_quality at %s' % url)

		result = self.get_video_info(vid)
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoCollegehumor)

if __name__ == '__main__':
	VideoCollegehumor.test()
