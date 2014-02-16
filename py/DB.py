#!/usr/bin/python

'''
	Class for facilitating communication with a sqlite database.
'''

from os   import path, getcwd, sep as ossep
from sys  import stderr
from time import sleep, gmtime, strftime

# Find location of database file
DB_FILE = 'database.db'
if getcwd().replace(ossep, '').endswith('py'):
	DB_FILE = path.join('..', 'database.db')

try:
	import sqlite3
except ImportError:
	import sqlite as sqlite3
	# This will throw an ImportError if sqlite isn't found

'''
	Database schema.
	Keys are table names, values are rows.
'''
SCHEMA = {
	'albums' :
		'name       text,' +    # Name of the album (unique per host)
		'url        text,' +    # Source
		'host       text,' +    # Name of site
		'ready      integer,' + # If album is completed
		'pending    integer,' + # If album is not completed
		'filesize   integer,' + # Total bytes for all content
		'path       text primary key,' + # Combination of host_name
		'created    integer,' + # Date created
		'modified   integer,' + # Date last modified
		'accessed   integer,' + # Date accessed
		'count      integer,' + # Number of medias in album
		'zip        text,'    + # Link to zip file
		'views      integer,' + # Number of views
		'metadata   text,' +    # Info about the album
		'author     text,' +    # IP of user who ripped it
		'reports    integer',   # Number of reports

	'medias' :
		'album_id   integer,' + # rowid of album
		'i_index    integer,' + # Index image appears in album
		'url        text,' +    # Source
		'valid      integer,' + # If image is valid, downloaded, viewable
		'error      text,' +    # If any errors occurred while downloading
		'type       text,' +    # Media type: image,video,thread
		'image_name text,' +    # Filename of image, exists in album's path
		'width      integer,' + # Image width
		'height     integer,' + # Image height
		'filesize   integer,' + # Size of image
		'thumb_name text,' +    # Filename of thumbnail, exists in album's path + /thumbs/
		't_width    integer,' + # Thumb width
		't_height   integer,' + # Thumb height
		'metadata   text,' +    # Info about image
		'foreign key(album_id) references albums(rowid),' +
		'primary key(album_id, i_index)',

	'urls' :
		'album_id  integer,' + # rowid of album
		'i_index   integer,' +  # Index image appears in album
		'url       text,' +     # source URL
		'saveas    text,' +     # What the ripper thinks the file should be saved as
		'type      text,' +     # Media type
		'metadata  text,' +     # Info about image
		'added     integer,' +  # Date added to DB
		'pending   integer,' +  # Current state of url
		'primary key(album_id, i_index)',

	'sites' :
		'host      text primary key,' + # Host name
		'available integer,' + # If host is available
		'message   text,' +    # Message if not available
		'checked   integer',   # Date last checked for availability

	'reports' :
		'album    text,' +
		'user     text,' +
		'message  text,' +
		'foreign key(album) references albums(path),' +
		'primary key(album, user)',

	'blacklist' :
		'host    text,' + # Name of host 
		'album   text,' + # Name of album
		'reason  text,' + # Reason for blacklist
		'admin   text,' + # IP of admin blacklisting
		'primary key(host, album)',

	'users' :
		'ip              text primary key,' + # IP of user
		'warning_message text,' +    # Warning message to display to user
		'warnings        integer,' + # Number of times user has been warned
		'warned          integer,' + # Date user was last warned
		'banned          integer,' + # If user is banned
		'banned_reason   text,' +    # Reason for banning
		'banned_url      text',      # URL user was banned for

	'admins' :
		'username text primary key,' +
		'cookie   text',

	'config' :
		'key   text primary key,' +
		'value text',

	'videos' :
		'accessed   integer,' +
		'author     text,' +    # IP of user who ripped it
		'url        text',
}

'''
	Index schema.
	Keys are table name, values are columns in index (separated by commas)
'''
INDICES = {
	'albums' : 'ready',
	'albums' : 'host',
	'albums' : 'created',
	'albums' : 'accessed',
	'albums' : 'views',
	'albums' : 'author',
	'medias' : 'album_id',
	'medias' : 'status',
	'medias' : 'path',
	'medias' : 'url',
	'config' : 'key'
}


class DB:
	'''
		Easy interface for interacting with database.
	'''

	def __init__(self):
		'''
			Connect to database, intializing it if needed.
		'''
		self.logger = stderr
		need_to_create = False
		if path.exists(DB_FILE):
			self.debug('__init__: connecting to database file: %s' % DB_FILE)
		else:
			need_to_create = True
			self.debug('__init__: database file (%s) not found, creating...' % DB_FILE)

		self.conn = sqlite3.connect(DB_FILE)
		self.conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
		if need_to_create:
			# Create tables
			for table in SCHEMA:
				self.create_table(table, SCHEMA[table])

			for index in INDICES:
				self.create_index(index, INDICES[index])
			# Commit
			self.commit()


	def debug(self, text):
		'''
			Prints text to stderr.
			Also prints to self.logger if different than stderr
		'''
		tstamp = strftime('[%Y-%m-%dT%H:%M:%SZ]', gmtime())
		text = '%s DB: %s' % (tstamp, text)
		self.logger.write('%s\n' % text)
		if self.logger != stderr:
			stderr.write('%s\n' % text)
			stderr.flush()

	def create_table(self, table_name, schema):
		'''
			Creates table in database if it doesn't already exist.
			Does not commit!
			Args:
				table_name: Name of the table
				schema: Technically the "values" of the schema. 
				        See global SCHEMA for formatting info.
		'''
		cur = self.conn.cursor()

		hit_keys = False
		rows = []
		keys = []
		for row in schema.split(','):
			fields = row.split(' ')
			if fields[0].lower() in ['primary', 'foreign']:
				hit_keys = True
			if hit_keys:
				keys.append(row)
			else:
				rows.append('%s %s' % (fields[0].rjust(16), ' '.join(fields[1:]).strip()))

		i = 0
		while i < len(keys):
			if '(' in keys[i] and ')' not in keys[i]:
				keys[i] = '%s,%s' % (keys[i], keys.pop(i+1))
			else:
				i += 1

		query = 'create table if not exists %s' % table_name
		query = '%s(\n%s%s\n%s)' % (query, ',\n'.join(rows), ',' if len(keys) > 0 else '', ',\n'.join(keys))
		cur.execute(query)
		cur.close()

	def create_index(self, index, key, name=None):
		'''
			Creates index on table if it doesn't exist.
			Does not commit!
		'''
		cur = self.conn.cursor()
		if name == None:
			name = '%s_%s' % (index, key.replace(',', '_'))
		query = '''
			create index 
				if not exists 
				%s on %s(%s)
		''' % (name, index, key)
		cur.execute(query)
		cur.close()
	
	def commit(self):
		'''
			Attempts to commit to DB, if fails, waits 100ms and tries again.
			Useful for when other instances are connected/commiting and DB is locked.
		'''
		while True:
			try:
				self.conn.commit()
				return
			except Exception, e:
				self.debug('failed to commit (%s), retrying...' % str(e))
				sleep(0.1)
	
	def insert(self, table, values):
		'''
			Inserts row into database.
			Does not commit!

			Args:
				table: Name of table to insert into
				values: array/tuple of values to insert

			Returns:
				The id of the inserted row.

			Raises:
				Exception if problems ocucrred while inserting into db.
		'''
		cur = self.conn.cursor()
		questions = ','.join(['?'] * len(values))
		query = '''
			insert into 
				%s 
				values (%s)
		''' % (table, questions)
		result = cur.execute(query, values)
		last_row_id = cur.lastrowid
		cur.close()
		return last_row_id
	
	def count(self, table, where='', values=[]):
		'''
			Counts number of results of a query.

			Args:
				table: Name of table to query
				where: Optional. Where statement, i.e. ("row_id > 5").
				values: Optional. Used to insert values into question 
				        marks found in where ('table', 'row_id > ?', [5])
			Returns:
				Number of rows found in query.

			Raises:
				Exception if errors occurred while querying database
		'''
		cur = self.select('count(*)', table, where=where, values=values)
		result = cur.fetchone()
		cur.close()
		return result[0]
	
	def select(self, what, table, where='', values=[]):
		'''
			Performs a SELECT query on a table.

			Args:
				what: The select field(s) to query (e.g. "id" or "id, name", or "count(name)")
				where: Optional. Where condition. (e.g. "id > 5")
				values: Optional. Values to insert into where condition's question marks.

			Returns:
				Cursor object result from query
			Raises:
				Exception if errors occurred while querying database.
			'''
		cur = self.conn.cursor()
		query = '''
			select
				%s
				FROM
				%s
		''' % (what, table)
		if where != '':
			query += '''
				WHERE %s
			''' % where
		return cur.execute(query, values)
	
	def select_one(self, what, table, where='', values=[]):
		'''
			Selects the first column of the first row of a SELECT query
			Returns the first column, or None if no rows were returned.
		'''
		ex = self.select(what, table, where, values).fetchone()
		if ex == None:
			return None
		return ex[0]

	def delete(self, table, where, values=[]):
		'''
			Deletes row(s) from database.

			Args:
				table: Table
				where: where condition
				values: Values to insert into where condition
		'''
		cur = self.conn.cursor()
		query = '''
			delete from %s
				where %s
			''' % (table, where)
		cur.execute(query, values)
		cur.close()
	
	def update(self, table, changes, where='', values=[]):
		'''
			Updates row(s) in database.

			Args:
				table: Table
				changes: What to set, e.g. "id = 3" or "id = 3, name = 'hey'"
				where: Where condition to decide what rows to update
				values: Values to insert into where condition
		'''
		cur = self.conn.cursor()
		if where != '':
			where = 'where %s' % where
		query = '''
			update %s
				set %s
				%s
		''' % (table, changes, where)
		cur.execute(query, values)
		cur.close()

	def get_config(self, key):
		'''
			WARNING: Expects a "config" table of schema (key text primary key, value text)
			Returns the config value for a specified key.

			Args:
				key: The key to look up
			Returns:
				Value for key in config, or None if no value is found
		'''
		cur = self.conn.cursor()
		query = '''
			select value
				from config
				where key = "%s"
		''' % key
		execur = cur.execute(query)
		result = execur.fetchone()
		cur.close()
		if result == None:
			return None
		return result[0]

	def set_config(self, key, value):
		'''
			Sets config value for a key.

			Args:
				key: Key
				value: Value
		'''
		cur = self.conn.cursor()
		query = '''
			insert or replace into
				config (key, value)
				values (?, ?)
		'''
		execur = cur.execute(query, [key, value])
		result = execur.fetchone()
		self.commit()
		cur.close()

if __name__ == '__main__':
	db = DB()
	print 'saving "yes" to config key "test"...'
	db.set_config('test', 'yes')
	print 'db.get_config("test") = "%s"' % db.get_config('test')
	db.create_table('videos', SCHEMA['videos'])
	album_id = db.insert('videos', [11, 'http://what', 'damn'])
	print album_id
	db.commit()