#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class VideoSeenive(VideoBase):

	@staticmethod
	def get_host():
		return 'seenive'

	@staticmethod
	def can_rip(url):
		return 'seenive.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://seenive.com/v/1031116119903268864'

	def rip_video(self):
		r = self.httpy.get(self.url)
		if not 'source src="' in r:
			raise Exception('could not find source src=" at ' % self.url)
		vid = self.httpy.between(r, 'source src="', '"')[0]

		meta = self.httpy.get_meta(vid)
		filesize = meta.get('Content-Length', 0)
		filetype = meta.get('Content-Type', 'unknown')
		if not filetype.startswith('video/'):
			raise Exception('content-type (%s) not "video/" at %s' % (filetype, vid))
		else:
			filetype = filetype.replace('video/', '').replace('x-', '')
		return (vid, filesize, filetype)

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		# Check that we can hit the host
		url = 'http://www.seenive.com'
		r = httpy.get(url)
		if len(r) == 0:
			raise Exception('unable to get content at %s' % url)

		# Try to rip the sample video
		url = VideoSeenive.get_sample_url()
		v = VideoSeenive(url)
		(url, filesize, filetype) = v.rip_video()
		print url, filesize, filetype

		# Assert we got the video
		if filesize == 0 or filetype == 'unknown':
			return 'unexpected filesize (%s) or filetype (%s) at %s' % (filesize, filetype, url)
		return None

if __name__ == '__main__':
	VideoSeenive.test()
