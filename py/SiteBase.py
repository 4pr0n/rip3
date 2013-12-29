#!/usr/bin/python

from DB import DB
from Httpy import Httpy
from calendar import timegm
from time import gmtime
from os import path

class SiteBase(object):

	def __init__(self, url):
		if not self.can_rip(url):
			raise Exception('ripper (%s) cannot rip URL (%s)' % (self.__class__.__name__, url))
		self.url = url
		self.url = self.sanitize_url()
		self.album_name = self.get_album_name()
		self.db = DB()
		self.httpy = Httpy()
		try:
			self.album_id = self.db.select_one('rowid', 'albums', 'host = ? and name = ?', [self.get_host(), self.get_album_name()])
			# Album already exists
			self.album_exists = True
		except:
			self.path = path.join('rips', '%s_%s' % (self.get_host(), self.album_name))
			now = timegm(gmtime())
			values = [
				self.album_name, # path
				self.url,        # source
				self.get_host(), # host
				0,    # ready
				0,    # pending
				0,    # filesize
				self.path, # path
				now,  # created
				now,  # modified
				now,  # accessed
				0,    # count
				None, # zip
				0,    # views
				None  # metadata
			]
			self.album_id = self.db.insert('albums', values)
			self.album_exists = False
		# Add album to DB, store album rowid in self.album_id
		pass

	@staticmethod
	def get_ripper(url):
		# TODO Return instantiated class for the ripper
		rippers = [SiteImagefap]
		for ripper in rippers:
			if ripper.can_rip(url):
				return ripper
		raise Exception('no compatible ripper found')

	''' Methods for getting info about the album '''
	@staticmethod
	def can_rip(url):
		raise Exception('can_rip() not overridden by inheriting class')
		
	def sanitize_url(self, url):
		raise Exception('sanitize_url() not overridden by inheriting class')

	def get_album_name(self, url):
		raise Exception('get_album_name() not overridden by inheriting class')

	def get_host(self, url):
		raise Exception('get_host() not overridden by inheriting class')

	def get_urls(self):
		'''
			Return list of urls for the album.
			Returns:
				Either:
					List of str's, each item is the URL to the image, or
					List of dict's, each dict has 'url', 'saveas', and/or 'metadata'.
						List of dict's contains None in fields as needed
		'''
		raise Exception('get_urls() not overridden by inheriting class')

	''' Methods for altering the state of the album in the DB '''
	def start(self):
		'''
			Get list of URLs, add to database, mark album as pending to be ripped
		'''
		if self.album_exists:
			# Don't re-rip an album
			raise Exception('album already exists')

		urls = self.get_urls()
		# Format URLs to contain all required info
		urls = SiteBase.format_urls(urls)

		if len(urls) == 0:
			# Can't rip if we don't have URLs
			raise Exception('no URLs returned from %s' % self.url)

		# Add URL to list of urls to be downloaded
		now = timegm(gmtime())
		for url_dict in urls:
			values = [
					self.album_id,
					url_dict['index'],
					url_dict['url'],
					url_dict['saveas'],
					url_dict['type'],
					url_dict['metadata'],
					now
				]
			self.db.insert('urls', values)
		# Mark album as pending
		self.db.update('albums', 'pending = 1, count = ?', 'rowid = ?', [len(urls), self.album_id])
		# Commit
		self.db.commit()

	@staticmethod
	def get_saveas(url, index):
		saveas = url[url.rfind('/')+1:]
		for c in ['?', '&', '#']:
			if c in saveas:
				saveas = saveas[:saveas.find(c)]
		saveas = '%03d_%s' % (index, saveas)
		return saveas

	@staticmethod
	def get_type(url):
		ext = url[url.rfind('.')+1:].lower()
		if ext in ['mp4', 'flv', 'wmv', 'mpg']:
			return 'video'
		elif ext in ['jpg', 'jpeg', 'png', 'gif']:
			return 'image'
		elif ext in ['html']:
			return 'html'
		elif ext in ['txt']:
			return 'text'
	
	@staticmethod
	def format_urls(urls):
		# Format list of urls as expected
		# We need url, saveas, type, and metadata
		real_urls = []
		for (index, url) in enumerate(urls):
			if type(url) == str:
				# Just a list of URLs. Add other data as needed
				real_urls.append({
					'url'      : url,
					'index'    : index,
					'metadata' : None,
					'saveas'   : SiteBase.get_saveas(url, index),
					'type'     : SiteBase.get_type(url),
				})
			elif type(url) == dict:
				if 'metadata' not in url:
					url['metadata'] = None
				if 'saveas' not in url:
					url['saveas'] = SiteBase.get_saveas(url['url'], index)
				if 'type' not in url:
					url['type'] = SiteBase.get_type(url['url'])
				if 'index' not in url:
					url['index'] = index
				real_urls.append(url)
		del urls
		return real_urls

if __name__ == '__main__':
	pass
