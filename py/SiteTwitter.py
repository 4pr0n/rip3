#!/usr/bin/python

from SiteBase import SiteBase

from json import loads
from time import sleep, time as timetime
from threading import Thread
from urllib import quote

class SiteTwitter(SiteBase):
	BATCH_USER   = 200
	BATCH_SEARCH = 100
	SLEEP_TIME   = 2.5

	MAX_REQUESTS_PER_RIP = 5

	@staticmethod
	def get_host():
		return 'twitter'

	@staticmethod
	def can_rip(url):
		return 'twitter.com/' in url

	@staticmethod
	def get_sample_url():
		#return 'https://twitter.com/bieberswifexo/media'
		return 'https://twitter.com/purrbunny/media'
		#return 'https://twitter.com/search?q=%23TittyTuesday&src=typd'

	def sanitize_url(self):
		# Instance variables to make parsing easier
		self.twitter_user   = None # Twitter username
		self.twitter_search = None # Search text

		url = self.url
		if 'twitter.com/search' in url:
			# Search
			if not 'q=' in url:
				raise Exception('twitter.com/search requires q=')
			q = url[url.find('q=')+2:]
			q = q.split('&')[0]
			self.twitter_search = q
		else:
			# User
			user = url[url.find('twitter.com/')+len('twitter.com/'):]
			user = user.split('/')[0]
			user = user.split('?')[0]
			user = user.split('#')[0]
			self.twitter_user = user
			self.url = 'https://twitter.com/%s' % user

	def get_album_name(self):
		if self.twitter_user != None:
			return self.twitter_user
		elif self.twitter_search != None:
			return 'search_%s' % SiteBase.fs_safe(self.twitter_search)
		raise Exception('url was neither a twitter user nor a twitter search')


	def set_access_token(self):
		'''
			Gets required Bearer access_token, sets in self.access_token
			Raises exception if unable to get token
		'''
		# Get authorization token
		auth_token = self.db.get_config('twitter_key')
		if auth_token == None:
			raise Exception('required twitter auth token not found')

		headers = {
				'Authorization' : 'Basic %s' % auth_token,
				'Content-Type'  : 'application/x-www-form-urlencoded;charset=UTF-8',
				'User-agent'    : 'derv\'s ripe and zipe'
			}
		postdata = {
			'grant_type' : 'client_credentials'
		}
		r = self.httpy.post('https://api.twitter.com/oauth2/token', postdata=postdata, headers=headers)
		json = loads(r)
		if not 'access_token' in json:
			raise Exception('unable to get access_token from twitter')
		self.access_token = json['access_token']


	def check_rate_limit(self, resource, api):
		'''
			Checks that it's OK to rip this album
			Raises exception if rip has to wait
		'''
		url = 'https://api.twitter.com/1.1/application/rate_limit_status.json?resources=%s' % quote(resource, '')
		headers = {
				'Authorization' : 'Bearer %s' % self.access_token,
				'Content-Type'  : 'application/x-www-form-urlencoded;charset=UTF-8',
				'User-agent'    : 'derv\'s ripe and zipe'
			}
		r = self.httpy.get_extended(url, headers=headers)
		json = loads(r)
		stats = json['resources'][resource][api]
		remaining = stats['remaining']
		if remaining < 20: # Within 20 of hitting rate limit, stop now
			# Not enough requests remaining to rip!
			now = int(timetime())
			diff = stats['reset'] - now # Seconds until reset
			dtime = ''
			if diff > 3600:
				dtime = '%d hours ' % (diff / 3600)
				diff %= 3600
			if diff > 60:
				dtime += '%d min ' % (diff / 60)
				diff %= 60
			if dtime == '' or diff != 0:
				dtime += '%d sec' % diff
			raise Exception('twitter is rate-limited, try again in %s' % dtime)


	def get_urls(self):
		# Get access token and store in self.access_token
		self.set_access_token()

		# Check the rate limits
		if self.twitter_user != None:
			self.check_rate_limit('search', '/search/tweets')
		elif self.twitter_search != None:
			self.check_rate_limit('statuses', '/statuses/user_timeline')

		self.results = []
		headers = {
				'Authorization' : 'Bearer %s' % self.access_token,
				'Content-Type'  : 'application/x-www-form-urlencoded;charset=UTF-8',
				'User-agent'    : 'derv\'s ripe and zipe'
			}
		max_id = '0'
		for page in xrange(0, SiteTwitter.MAX_REQUESTS_PER_RIP):
			url = self.get_request(max_id=max_id)
			# Using get_extended since this is an https request
			r = self.httpy.get_extended(url, headers=headers, retry=0)
			try:
				json = loads(r)
			except Exception, e:
				raise Exception('invalid response from twitter (%s)' % str(e))

			# Check for errors
			if 'errors' in json:
				raise Exception('twitter error: %s' % json['errors']['message'])
			if 'statuses' not in json and len(json) == 0:
				break # No (more) results

			# Search returns list of tweets in 'statuses' key
			if type(json) == dict:
				json = json.get('statuses', [])
			# User returns just the list of tweets

			max_id = '0'
			for tweet in json:
				max_id = str(tweet.get('id', 1) - 1)
				self.parse_tweet(tweet)

			# Load more if needed
			if True or max_id == '0':
				break
			sleep(SiteTwitter.SLEEP_TIME)

		# Wait for any threads to finish
		while len(self.threads) > 0:
			sleep(0.1)

		return self.results


	def get_request(self, max_id='0'):
		'''
			Returns URL to twitter API
			Either a user request or search request depending on self.twitter_[user/search]
		'''
		if self.twitter_user != None:
			req  = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
			req += '?screen_name=%s' % self.twitter_user
			req += '&include_entities=true'
			req += '&exclude_replies=true'
			req += '&trim_user=true'
			req += '&include_rts=false'
			req += '&count=%d' % SiteTwitter.BATCH_USER
		elif self.twitter_search != None:
			req  = 'https://api.twitter.com/1.1/search/tweets.json'
			req += '?q=%s' % self.twitter_search
			req += '&include_entities=true'
			req += '&result_type=recent'
			req += '&count=%d' % SiteTwitter.BATCH_SEARCH
		if max_id != '0':
			req += '&max_id=%s' % max_id
		return req


	def parse_tweet(self, tweet):
		'''
			Parses urls from tweet, adds to self.results
		'''
		if 'entities' not in tweet:
			return
		entities = tweet['entities']

		# Get media(s)
		try:
			for media in entities['media']:
				url = media['media_url']
				if '.twimg.com/' in url:
					url = '%s:large' % url
				if not url in self.results:
					self.results.append(url)
		except:
			pass
		# Get expanded_url(s)
		try:
			for urlchunk in entities['urls']:
				url = urlchunk['expanded_url']
				self.handle_url(url)
		except:
			pass


	def handle_url(self, url):
		'''
			Parses URL, adds to self.results
			Or creates thread to find url and do the same
		'''
		# Check for direct link to image
		ext = url[url.rfind('.')+1:].lower()
		if ext in ['jpg', 'jpeg', 'gif', 'png']:
			# Direct link to image
			if not url in self.results:
				self.results.append(url)
			return

		# Check if the site is worth checking
		if 'twitpic.com/' in url or \
		   'tumblr.com/'  in url or \
		   'vine.co/'     in url:
			# Images on these sites can be easily parsed
			# Create new thread to retrieve the page content & parse the URL
			while len(self.threads) >= self.max_threads:
				sleep(0.1)
			self.threads.append(None)
			t = Thread(target=self.handle_url_thread, args=(url,))
			t.start()

	def handle_url_thread(self, url):
		'''
			Retrieves content at url, tries to find media there
		'''
		try:
			# Get url
			r = self.httpy.get(url)
			imgs = []
			for metaname in ['twitter:player:stream', 'twitter:image']:
				if '<meta name="%s" content="' % metaname in r:
					imgs = self.httpy.between(r, '<meta name="%s" content="' % metaname, '"')
					break
				if '<meta name="%s" value="' % metaname in r:
					imgs = self.httpy.between(r, '<meta name="%s" value="' % metaname, '"')
					break
				if '<meta property="%s" content="' % metaname in r:
					imgs = self.httpy.between(r, '<meta property="%s" content="' % metaname, '"')
					break
			# Add to self.results
			for img in imgs:
				if img not in self.results:
					self.results.append(img)
		except Exception, e:
			pass
		self.threads.pop()

	@staticmethod
	def get_url_from_album_path(album):
		fields = album.split('_')
		if len(fields) < 2 or fields[0] != SiteTwitter.get_host():
			return None
		# Return url of album (if possible)
		if len(fields) == 2:
			return 'https://twitter.com/%s' % fields[1]
		return 'https://twitter.com/search?q=%s' % '_'.join(fields[1:])

	@staticmethod
	def test():
		from Httpy import Httpy
		httpy = Httpy()

		# Check we can hit the host
		url = 'http://twitter.com'
		r = httpy.get(url)
		if len(r.strip()) == 0:
			# Raise exception because the site is *very* broken, definitely can't rip from it if we can't hit the home page.
			raise Exception('unable to retrieve data from %s' % url)

		# Check ripper gets all images in an album
		url = SiteTwitter.get_sample_url()
		s = SiteTwitter(url)
		urls = s.get_urls()
		expected = 5
		if len(urls) < expected:
			# Returning non-None string since this may be a transient error.
			# Maybe the album was deleted but the ripper is working as expected.
			return 'expected at least %d images, got %d. url: %s' % (expected, len(urls), url)

		# Returning None because the ripper is working as expected. No issues found.
		return None

if __name__ == '__main__':
	print SiteTwitter.test()
