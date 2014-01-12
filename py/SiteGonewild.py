#!/usr/bin/python

from SiteBase import SiteBase

class SiteGonewild(SiteBase):

	@staticmethod
	def get_host():
		return 'gonewild'

	@staticmethod
	def can_rip(url):
		url = url.replace('http://', '')
		return url.startswith('gonewild:') and \
				url.count(':') == 1 and \
				SiteGonewild.valid_username(url.split(':')[1])

	@staticmethod
	def valid_username(user):
		alpha = 'abcdefghijklmnopqrstuvwxyz-_0123456789'
		for c in user:
			if not c.lower() in alpha:
				return False
		return len(user) >= 3

	@staticmethod
	def get_sample_url():
		return 'gonewild:thatnakedgirl'

	def sanitize_url(self):
		self.url = self.url.replace('http://', '')
		self.url = self.url.lower()

	def get_album_name(self):
		return self.url.split(':')[-1]

	def start(self):
		'''
			Overriding SiteBase's start() method for unique ripping logic
		'''
		# We need a lot of libraries
		from ImageUtils import ImageUtils
		from calendar import timegm
		from shutil import copy2, rmtree
		from time import gmtime
		from os import path, walk, environ, getcwd
		from json import loads

		savedir = path.join('rips', self.path)
		if getcwd().endswith('py'):
			savedir = path.join('..', savedir)

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

		user = self.url.split(':')[-1]

		# Search for username (with proper case) on site
		gwapi = self.db.get_config('gw_api')
		if gwapi == None:
			raise Exception('unable to rip gonewild albums: gw_api is null')
		r = self.httpy.get('%s?method=search_user&user=%s' % (gwapi, user))
		json = loads(r)
		found = False
		for jsonuser in json['users']:
			if jsonuser.lower() == user.lower():
				found = True
				user = jsonuser
				break

		gwroot = self.db.get_config('gw_root')
		if gwroot == None:
			raise Exception('unable to rip gonewild albums: gw_root is null')
		userroot = path.join(gwroot, user)
		# Check if we can actually rip this user
		if not found or not path.exists(userroot):
			return {
				'error' : 'unable to rip user (not archived)'
			}

		# Create subdirs
		ImageUtils.create_subdirectories(path.join(savedir, 'thumbs'))

		# Copy images to /rips/, get values that need to be inserted into db (insertmany)
		insertmany = []
		already_got = []
		filesize = 0
		for root, subdirs, files in walk(userroot):
			if root.endswith('thumbs'): continue
			for filename in sorted(files):
				f = path.join(root, filename)
				n = filename
				if not root.endswith(userroot):
					# It's a subidr, save the file accordingly
					n = '%s_%s' % (root[root.rfind('/')+1:], filename)

				# Avoid duplicates
				no_post = n[n.rfind('_')+1:]
				if no_post in already_got: continue
				already_got.append(no_post)

				n = '%03d_%s' % (len(insertmany) + 1, n)
				saveas = path.join(savedir, n)

				# Copy & get size
				try:
					copy2(f, saveas)
					(width, height) = ImageUtils.get_dimensions(saveas)
				except Exception, e:
					# image can't be parsed, probably corrupt. move on.
					continue

				# Create thumbnail
				tsaveas = path.join(savedir, 'thumbs', n)
				try:
					(tsaveas, twidth, theight) = ImageUtils.create_thumbnail(saveas, tsaveas)
				except Exception, e:
					# Failed to create thumb
					tsaveas = '/'.join(['ui', 'images', 'nothumb.png'])
					twidth = theight = 160

				filesize += path.getsize(saveas)
				# Add to list of values to insert into DB
				insertmany.append( [
						self.album_id,        # album_id, currently None
						len(insertmany) + 1,  # i_index
						'',                   # url TODO
						1,                    # valid
						None,                 # error
						SiteBase.get_type(saveas), # type
						n,                    # image_name
						width,                # img width
						height,               # img height
						path.getsize(saveas), # filesize
						path.basename(tsaveas), # thumb_name
						twidth,               # thumb width
						theight,              # thumb height
						None                  # metadata
					] )

		if len(insertmany) == 0:
			# Failed to get any images
			rmtree(savedir)
			return {
				'error' : 'unable to rip %s' % self.url
			}

		# Insert album into DB
		now = timegm(gmtime())
		values = [
			self.album_name, # name
			self.url,        # source url
			self.get_host(), # host
			1,         # ready
			0,         # pending
			filesize,  # filesize
			self.path, # path
			now,       # created
			now,       # modified
			now,       # accessed
			len(insertmany), # count
			None,      # zip
			0,         # views
			None,      # metadata
			environ.get('REMOTE_ADDR', '0.0.0.0'), # author
			0          # reports
		]
		self.album_id = self.db.insert('albums', values)

		# Set album_id on all medias being inserted (now that we have it)
		for tup in insertmany:
			tup[0] = self.album_id

		# Insert all medias into DB
		cursor = self.db.conn.cursor()
		qs = ','.join(['?'] * len(insertmany[0]))
		cursor.executemany('insert into medias values (%s)' % qs, insertmany)
		self.db.commit()
		cursor.close()
		return {
			'album_id' : self.album_id,
			'album'    : self.album_name,
			'url'      : self.url,
			'host'     : self.get_host(),
			'path'     : self.path,
			'count'    : len(insertmany)
		}

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteGonewild.get_host():
			return None
		return album.replace('_', ':')

	@staticmethod
	def test():
		from os import path
		sgw = SiteGonewild('gonewild:aappleby9')
		gwroot = sgw.db.get_config('gw_root')
		if gwroot == None:
			raise Exception('unable to rip gonewild albums: gw_root is null')
		if not path.exists(gwroot):
			raise Exception('unable to rip gonewild albums: gw_root does not exist')
		return None

if __name__ == '__main__':
	SiteGonewild.test()
