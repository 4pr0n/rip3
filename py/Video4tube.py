#!/usr/bin/python

from VideoBase import VideoBase

class Video4tube(VideoBase):

	@staticmethod
	def get_host():
		return '4tube'

	@staticmethod
	def can_rip(url):
		return '4tube.com/videos' in url

	@staticmethod
	def get_sample_url():
		return 'http://www.4tube.com/videos/146975/sexpot-mary-jane-johnson-gets-her-tight-snatch-slammed'

	def rip_video(self):
		r = self.httpy.get(self.url)
		qualities = self.httpy.between(r, 'sources: [', ']')
		if len(qualities) == 0:
			raise Exception('no "sources:" found at %s' % self.url)
		qualities = qualities[0].split(',')
		vidids = self.httpy.between(r, 'idMedia: ', ',')
		if len(vidids) == 0:
			raise Exception('no "idMedia" found at %s' % self.url)
		posturl = 'http://tkn.4tube.com/%s/desktop/%s' % (vidids[0], '+'.join(qualities))
		headers = {
			'Origin' : '4tube.com'
		}

		r = self.httpy.post(posturl, postdata='{}', headers=headers)

		from json import loads
		from os import environ
		json = loads(r)
		temp = json[qualities[-1]]['token']
		vid = temp
		'''
		vid = temp[:temp.find('&ip=')]
		vid += '&ip=%s' % environ.get('REMOTE_ADDR', '127.0.0.1')
		temp = temp[temp.find('&ip=')+4:]
		vid += temp[temp.find('&'):]
		'''

		result = self.get_video_info(vid)
		result['poster'] = None # Beeg doesn't provide video splash images
		#result['no_video'] = True # Don't embed video
		return result

	@staticmethod
	def test():
		return VideoBase.test_ripper(Video4tube)

if __name__ == '__main__':
	Video4tube.test()
