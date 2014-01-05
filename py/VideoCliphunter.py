#!/usr/bin/python

from VideoBase import VideoBase

from json import loads

class VideoCliphunter(VideoBase):

	@staticmethod
	def get_host():
		return 'cliphunter'

	@staticmethod
	def can_rip(url):
		return 'cliphunter.com/w/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.cliphunter.com/w/1803175/IHaveAWife_Madison_Ivy'

	def rip_video(self):
		url = self.url
		if 'm.cliphunter.com' in url:
			url = url.replace('m.cliphunter.com', 'cliphunter.com')

		r = self.httpy.get(url)
		if not "var flashVars = {d: '" in r:
			raise Exception('could not find flashVars at %s' % url)
		json = loads(self.httpy.between(r, "var flashVars = {d: '", "'")[0].decode('base64'))

		jsonurl = loads(json['url'].decode('base64'))
		vid = self.decrypt(jsonurl['u']['l'])

		meta = self.httpy.get_meta(vid)
		filesize = meta.get('Content-Length', 0)
		filetype = meta.get('Content-Type', 'unknown')
		if not filetype.startswith('video/'):
			raise Exception('content-type (%s) not "video/" at %s' % (filetype, vid))
		else:
			filetype = filetype.replace('video/', '').replace('x-', '')
		return (vid, filesize, filetype)

	def decrypt(self, txt):
		'''
			Decrypts cliphunter URL
		'''
		d = {'$': ':', '&': '.', '(': '=', '-': '-', 
			 '_': '_', '^': '&', 'a': 'h', 'c': 'c', 
			 'b': 'b', 'e': 'v', 'd': 'e', 'g': 'f', 
			 'f': 'o', 'i': 'd', 'm': 'a', 'l': 'n', 
			 'n': 'm', 'q': 't', 'p': 'u', 'r': 's', 
			 'w': 'w', 'v': 'p', 'y': 'l', 'x': 'r', 
			 'z': 'i', '=': '/', '?': '?'
		}
		result = ''
		for char in txt:
			if char.isdigit():
				result += char
			elif char in d:
				result += d[char]
			else:
				raise Exception('do not have decryption for %s' % char)
		return result

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		# Check that we can hit the host
		url = 'http://www.cliphunter.com'
		r = httpy.get(url)
		if len(r) == 0:
			raise Exception('unable to get content at %s' % url)

		# Try to rip the sample video
		url = VideoCliphunter.get_sample_url()
		v = VideoCliphunter(url)
		(url, filesize, filetype) = v.rip_video()

		# Assert we got the video
		if filesize == 0 or filetype == 'unknown':
			return 'unexpected filesize (%s) or filetype (%s) at %s' % (filesize, filetype, url)
		return None

if __name__ == '__main__':
	VideoCliphunter.test()
