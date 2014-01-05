#!/usr/bin/python

from VideoBase import VideoBase

from urllib import unquote

class VideoMotherless(VideoBase):

	@staticmethod
	def get_host():
		return 'motherless'

	@staticmethod
	def can_rip(url):
		return 'motherless.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://motherless.com/FF6D765'

	def rip_video(self):
		r = self.httpy.get(self.url)
		if not "__fileurl = '" in r:
			raise Exception('could not find __fileurl= at ' % self.url)
		vid = self.httpy.between(r, "__fileurl = '", "'")[0]

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
		url = 'http://www.motherless.com'
		r = httpy.get(url)
		if len(r) == 0:
			raise Exception('unable to get content at %s' % url)

		# Try to rip the sample video
		url = VideoMotherless.get_sample_url()
		v = VideoMotherless(url)
		(url, filesize, filetype) = v.rip_video()
		print url, filesize, filetype

		# Assert we got the video
		if filesize == 0 or filetype == 'unknown':
			return 'unexpected filesize (%s) or filetype (%s) at %s' % (filesize, filetype, url)
		return None

if __name__ == '__main__':
	VideoMotherless.test()
