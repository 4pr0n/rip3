#!/usr/bin/python

'''
	Abstract interface for album rippers
'''

from DB import DB
from Httpy import Httpy
from calendar import timegm
from time import gmtime
from os import path, environ, listdir, getcwd

class SiteBase(object):

	'''
		Maximum images allowed per rip.
		Note: This can be overridden by inheriting subclasses
	'''
	MAX_IMAGES_PER_RIP = 500

	'''
		Maximum threads allowed at one time
		Used for retrieving URLs for sub-pages
	'''
	MAX_THREADS = 3

	def __init__(self, url):
		if not self.can_rip(url):
			# Don't instantiate if we can't rip it
			raise Exception('ripper (%s) cannot rip URL (%s)' % (self.__class__.__name__, url))
		self.url = url
		self.sanitize_url()
		self.album_name = self.get_album_name()
		self.db = DB()
		self.httpy = Httpy()
		self.max_threads  = self.MAX_THREADS
		self.threads      = []

		self.album_id = self.db.select_one('rowid', 'albums', 'host = ? and name = ?', [self.get_host(), self.get_album_name()])
		self.path     = self.db.select_one('path',  'albums', 'host = ? and name = ?', [self.get_host(), self.get_album_name()])

		if self.path == None:
			# Album does not exist.
			self.album_exists = False
			self.path = '%s_%s' % (self.get_host(), self.album_name)
		else:
			# Album already exists
			self.album_exists = True

	@staticmethod
	def get_ripper(url):
		'''
			Searches through all rippers in this directory for a compatible ripper.
			Args:
				url: URL to rip
			Returns:
				Uninstantiated class for the ripper that is compatible with the url.
			Raises:
				Exception if no ripper can be found, or other errors occurred
		'''
		for ripper in SiteBase.iter_rippers():
			if 'can_rip' in ripper.__dict__ and ripper.can_rip(url):
				return ripper
		raise Exception('no compatible ripper found')


	''' Below are methods for getting info about the album '''

	@staticmethod
	def can_rip(url):
		'''
			Returns:
				True if this ripper can rip the given URL, False otherwise
		'''
		raise Exception('can_rip() not overridden by inheriting class')
		
	def sanitize_url(self):
		pass # Do nothing, URL is fine.

	def get_album_name(self):
		'''
			Returns: Name of album unique for this ripper's host
		'''
		raise Exception('get_album_name() not overridden by inheriting class')

	def get_host(self):
		'''
			Returns the 'name' of this ripper's host
		'''
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


	''' Below are methods for altering the state of the album in the DB '''

	def start(self):
		'''
			Get list of URLs, add to database, mark album as pending to be ripped
		'''
		if self.album_exists:
			# Don't re-rip an album. Return info about existing album.
			return {
				'warning'  : 'album already exists',
				'album_id' : self.album_id,
				'album'    : self.album_name,
				'url'      : self.url,
				'host'     : self.get_host(),
				'path'     : self.path,
				'count'    : self.db.count('medias', 'album_id = ?', [self.album_id]),
				'pending'  : self.db.count('urls', 'album_id = ?', [self.album_id])
			}

		urls = self.get_urls()

		if len(urls) == 0:
			# Can't rip if we don't have URLs
			raise Exception('no URLs returned from %s (before formatting)' % self.url)

		# Enforce max images limit
		if len(urls) > self.MAX_IMAGES_PER_RIP:
			urls = urls[:self.MAX_IMAGES_PER_RIP]
		# Format URLs to contain all required info
		urls = SiteBase.format_urls(urls)

		if len(urls) == 0:
			# Can't rip if we don't have URLs
			raise Exception('no URLs returned from %s (after formatting)' % self.url)

		# Insert empty album into DB
		now = timegm(gmtime())
		values = [
			None,
			self.album_name, # name
			self.url,        # source url
			self.get_host(), # host
			0,    # ready
			1,    # pending
			0,    # filesize
			self.path, # path
			now,  # created
			now,  # modified
			now,  # accessed
			len(urls),  # count
			None, # zip
			0,    # views
			None, # metadata
			environ.get('REMOTE_ADDR', '0.0.0.0'), # author
			0     # reports
		]
		self.album_id = self.db.insert('albums', values)

		# Add URL to list of urls to be downloaded
		now = timegm(gmtime())
		insertmany = []
		for url_dict in urls:
			insertmany.append((
					self.album_id,
					url_dict['index'],
					url_dict['url'],
					url_dict['saveas'],
					url_dict['type'],
					url_dict['metadata'],
					now,   # Added date
					0      # Pending
				))
		q = '''
			insert into urls
			values (%s)
		''' %  ','.join(["%s" for i in range(len(insertmany[0]))])		
		cursor = self.db.conn.cursor()
		cursor.executemany(q, insertmany)
		self.db.commit()

		return {
			'album_id' : self.album_id,
			'album' : self.album_name,
			'url' : self.url,
			'host' : self.get_host(),
			'path' : self.path,
			'count' : len(urls)
		}


	@staticmethod
	def get_saveas(url, index):
		''' Strips extraneous characters from URL '''
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		if '&' in url: url = url[:url.find('&')]
		fields = url.split('/')
		while not '.' in fields[-1]: fields.pop(-1)
		saveas = '%03d_%s' % (index, fields[-1])
		return saveas

	@staticmethod
	def get_type(url):
		'''
			Args:
				url: The URL we are about to download
			Returns:
				The 'type' of medi at the URL (divined from file extension
				e.g. 'video', 'image', 'text' or 'html'
		'''
		ext = url[url.rfind('.')+1:].lower()
		if ext[:3] in ['mp4', 'flv', 'wmv', 'mpg']:
			return 'video'
		elif ext[:3] in ['jpg', 'jpe', 'png', 'gif']:
			return 'image'
		elif ext[:4] in ['html']:
			return 'html'
		elif ext[:3] in ['txt']:
			return 'text'
	
	@staticmethod
	def format_urls(urls):
		'''
			Handles response from ripper's get_urls() function.
			Automatically generates saveas and type if not given.

			Args:
			  urls: Either:
			        1. A list of URLs (list of str's)
			        2. A list of dicts containing 'url', 'index', 'metadata', 'saveas', and/or 'type'

			Returns:
				List of dicts containing url, index, metadata, saveas, and type
		'''
		# Format list of urls as expected
		# We need url, saveas, type, and metadata
		real_urls = []
		for (index, url) in enumerate(urls):
			if type(url) == str or type(url) == unicode:
				# Just a list of URLs. Add other data as needed
				real_urls.append({
					'url'      : url,
					'index'    : index + 1,
					'metadata' : None,
					'saveas'   : SiteBase.get_saveas(url, index + 1),
					'type'     : SiteBase.get_type(url),
				})
			elif type(url) == dict:
				if 'metadata' not in url:
					url['metadata'] = None
				if 'saveas' not in url:
					url['saveas'] = SiteBase.get_saveas(url['url'], index + 1)
				if 'type' not in url:
					url['type'] = SiteBase.get_type(url['url'])
				if 'index' not in url:
					url['index'] = index + 1
				real_urls.append(url)
		del urls
		return real_urls

	@staticmethod
	def iter_rippers():
		'''
			Iterator over all rippers in this directory
		'''
		if not getcwd().endswith('py'):
			prefix = 'py.'
		for mod in sorted(listdir(path.dirname(path.realpath(__file__)))):
			if not mod.startswith('Site') or not mod.endswith('.py') or mod.startswith('SiteBase'):
				continue
			mod = mod[:-3]
			try:
				ripper = __import__('%s%s' % (prefix, mod), fromlist=[mod]).__dict__[mod]
			except:
				# Don't use a prefix
				ripper = __import__(mod, fromlist=[mod]).__dict__[mod]
			yield ripper

	@staticmethod
	def get_supported_sites():
		result = []
		for ripper in SiteBase.iter_rippers():
			result.append(ripper.get_host())
		return result

	@staticmethod
	def get_url_from_path(album):
		return None

	@staticmethod
	def update_supported_sites_statuses():
		'''
			Runs 'test()' on every ripper.
			Updates database with the ripper's current status (available, errored, etc
		'''
		db = DB()
		cur = db.conn.cursor()
		for ripper in SiteBase.iter_rippers():
			if 'test' not in ripper.__dict__ or \
					'get_host' not in ripper.__dict__:
				continue
			host = ripper.get_host()
			available = -1
			message = ''
			try:
				ripper.test()
				available = 1
			except Exception, e:
				available = 0
				message = str(e)
			q = 'insert or replace into sites values (?, ?, ?, ?)'
			cur.execute(q, [host, available, message, timegm(gmtime())])
		db.commit()
		cur.close()

	@staticmethod
	def fs_safe(txt):
		safe = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
		return ''.join(c for c in txt if c in safe)

if __name__ == '__main__':
	'''
	url = 'http://www.imagefap.com/pictures/3150651/'
	Ripper = SiteBase.get_ripper(url)
	print Ripper.get_host()
	#print ripper.start()
	'''
	#print SiteBase.get_supported_sites()
	SiteBase.update_supported_sites_statuses()
