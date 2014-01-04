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
				Tuple:
					[0] video url
					[1] filesize
					[2] type
		'''
		raise Exception('get_sample_url() not overridden by inheriting class')

	@staticmethod
	def iter_rippers():
		'''
			Iterator over all video rippers in this directory
		'''
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
		for ripper in SiteBase.iter_rippers():
			if 'can_rip' in ripper.__dict__ and ripper.can_rip(url):
				return ripper
		raise Exception('no compatible ripper found')


