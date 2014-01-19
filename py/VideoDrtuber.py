#!/usr/bin/python

from VideoBase import VideoBase

class VideoDrtuber(VideoBase):

	@staticmethod
	def get_host():
		return 'drtuber'

	@staticmethod
	def can_rip(url):
		return 'drtuber.com' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.drtuber.com/video/103905/real-incest-with-drunk-sister'

	def rip_video(self):
		import hashlib
		from urllib import unquote
		r = self.httpy.get(self.url)
		params = "".join([x.replace("' + '", "") for x in self.httpy.between(r, "params += '", "';")])
		vkey = params.split('=')[-1]
		m = hashlib.md5()
		m.update(vkey + 'PT6l13umqV8K827')
		params += '&pkey=%s' % m.hexdigest()
		params = unquote(params)
		url = 'http://www.drtuber.com/player/config.php?' + params
		r = self.httpy.get(url)
		vids = self.httpy.between(r, '<video_file><![CDATA[', ']]></video_file>')
		if len(vids) == 0:
			raise Exception('no video_file found at %s' % url)
		vid = vids[0].replace('&amp;', '&')

		result = self.get_video_info(vid)
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoDrtuber)

if __name__ == '__main__':
	VideoDrtuber.test()
