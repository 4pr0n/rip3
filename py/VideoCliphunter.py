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

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

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
		return VideoBase.test_ripper(VideoCliphunter)

if __name__ == '__main__':
	VideoCliphunter.test()
