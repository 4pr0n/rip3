#!/usr/bin/python

from VideoBase import VideoBase

from json import loads

class VideoDailymotion(VideoBase):

	@staticmethod
	def get_host():
		return 'dailymotion'

	@staticmethod
	def can_rip(url):
		return 'dailymotion.com/' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.dailymotion.com/us?ff=1&urlback=%2Fvideo%2Fx3rhxg_keyra-augustina_redband'

	def rip_video(self):
		url = self.url
		# Bypass family filter
		back = url[url.find('dailymotion.com')+len('dailymotion.com'):]
		url = 'http://www.dailymotion.com/family_filter?enable=false&urlback=%s' % back
		r = self.httpy.get(url, headers={'family_filter' : 'off', 'masscast' : 'null'} )

		# Get twitter embed link
		if not '<meta name="twitter:player" value="' in r:
			raise Exception('unable to find video embed at %s' % url)
		embed = self.httpy.between(r, '<meta name="twitter:player" value="', '"')[0]
		r = self.httpy.get(embed)

		# Get info json
		if not 'var info = ' in r:
			raise Exception('unable to find var info at %s' % embed)
		jsonchunk = self.httpy.between(r, 'var info = ', 'fields = ')[0].strip()
		while jsonchunk.endswith(','): jsonchunk = jsonchunk[:-1]
		json = loads(jsonchunk)

		# Get video link
		vid = None
		for key in ['stream_h264_hd1080_url','stream_h264_hd_url', 'stream_h264_hq_url','stream_h264_url', 'stream_h264_ld_url']:
			if key in json and json[key] != None:
				vid = json[key]
				break
		if vid == None:
			raise Exception('unable to find stream at %s' % embed)

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(VideoDailymotion)

if __name__ == '__main__':
	VideoDailymotion.test()
