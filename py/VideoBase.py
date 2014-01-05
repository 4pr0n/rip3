#!/usr/bin/python

from Httpy import Httpy

class VideoBase(object):

	def __init__(self, url):
		if not self.can_rip(url):
			# Don't instantiate if we can't rip it
			raise Exception('ripper (%s) cannot rip URL (%s)' % (self.__class__.__name__, url))
		self.url = url
		self.httpy = Httpy()

	@staticmethod
	def get_host():
		'''
			Returns the 'name' of this video ripper's host
		'''
		raise Exception('get_host() not overridden by inheriting class')

	@staticmethod
	def can_rip(url):
		'''
			Returns:
				True if this ripper can rip the given URL, False otherwise
		'''
		raise Exception('can_rip() not overridden by inheriting class')

	@staticmethod
	def get_sample_url():
		'''
			Returns a test URL to be used by test()
		'''
		raise Exception('get_sample_url() not overridden by inheriting class')

	def rip_video(self):
		'''
			Gets info about the video at self.url
			Returns:
				dict containing keys:
					['url']    video url
					['size']   filesize of video
					['type']   type of video (mp4/flv)
					['poster'] image showing preview of album (optional)
		'''
		raise Exception('rip-video() not overridden by inheriting class')

	def get_video_info(self, url):
		'''
			Asserts URL is valid and points to video
			Returns dict containing url, size, and type
		'''
		meta = self.httpy.get_meta(url)
		filesize = int(meta.get('Content-Length', '0'))
		filetype = meta.get('Content-Type', 'unknown')
		if not filetype.startswith('video/'):
			raise Exception('content-type (%s) not "video/" at %s' % (filetype, vid))
		else:
			filetype = filetype.replace('video/', '').replace('x-', '')
		return {
			'url' : url,
			'size' : filesize,
			'type' : filetype,
			'host' : self.get_host(),
			'source' : self.url
		}

	@staticmethod
	def iter_rippers():
		'''
			Iterator over all video rippers in this directory
		'''
		from os import getcwd, listdir, path
		if not getcwd().endswith('py'):
			prefix = 'py.'
		for mod in listdir(path.dirname(path.realpath(__file__))):
			if not mod.startswith('Video') or not mod.endswith('.py') or mod.startswith('VideoBase'):
				continue
			mod = mod[:-3]
			try:
				ripper = __import__('%s%s' % (prefix, mod), fromlist=[mod]).__dict__[mod]
			except:
				# Don't use a prefix
				ripper = __import__(mod, fromlist=[mod]).__dict__[mod]
			yield ripper

	@staticmethod
	def get_ripper(url):
		'''
			Searches through all video rippers in this directory for a compatible ripper.
			Args:
				url: URL of video to rip
			Returns:
				Uninstantiated class for the ripper that is compatible with the url.
			Raises:
				Exception if no ripper can be found, or other errors occurred
		'''
		for ripper in VideoBase.iter_rippers():
			if 'can_rip' in ripper.__dict__ and ripper.can_rip(url):
				return ripper
		raise Exception('no compatible ripper found')

	@staticmethod
	def test_ripper(ripper):
		from Httpy import Httpy
		httpy = Httpy()

		# Try to rip the sample video
		url = ripper.get_sample_url()
		v = ripper(url)
		result = v.rip_video()
		print result

		# Assert we got the video
		if result.get('size', 0) == 0:
			return 'unexpected filesize (%s) at %s' % (filesize, filetype, url)
		if result.get('type', 'unknown') == 'unknown':
			return 'unexpected filetype (%s) at %s' % (filesize, filetype, url)
		return None

