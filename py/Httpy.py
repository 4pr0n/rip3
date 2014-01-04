#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
	HTTP/Web class.
	Holds commonly-used HTTP/web request/post methods.
"""

import urllib2, cookielib, urllib, httplib
from sys import stderr

class Httpy:

	def __init__(self, user_agent=None, debugging=False, logger=stderr):
		self.logfile = logger
		self.cj      = cookielib.CookieJar()
		self.opener  = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.Request = urllib2.Request
		self.urlopen = self.opener.open

		if user_agent != None:
			self.user_agent = user_agent
		else:
			self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:19.0) Gecko/20100101 Firefox/19.0'

	def log(self, text):
		self.logfile.write('Httpy: %s\n' % text)
		self.logfile.flush()

	def get_headers(self):
		return {
				'User-agent': self.user_agent
			}


	def get_meta(self, url):
		"""
			Reads file info (content type, length, etc) without downloading
		"""
		url = self.unshorten(url)
		try:
			req = urllib2.Request(url, headers=self.get_headers())
			site = self.urlopen(req)
		except Exception, e:
			self.log('get_meta(%s): Exception %s' % (url, str(e)))
			raise e
		return site.info()


	def unshorten(self, url):
		""" 
			Unshortens URL. Follows until no more redirects.
			Args:
				url: The url to unshorten

			Returns:
				Destination URL in case of redirect, otherwise same URL.
				Returns same URL in event of error/exception.
		"""
		try:
			req = urllib2.Request(url, headers=self.get_headers())
			site = self.urlopen(req)
		except Exception, e:
			self.log('unshorten(%s): Exception %s' % (url, str(e)))
			return url
		return site.url


	def validate(self, url):
		""" Check if a URL is valid """
		try:
			self.urlopen(url)
		except:
			return False
		return True


	def get(self, url, headers={}):
		"""
			Returns result of a GET request.
		"""
		headers = dict(headers.items() + self.get_headers().items())
		try:
			req = urllib2.Request(url, headers=headers)
			handle = self.urlopen(req)
		except Exception, e:
			self.log('get(%s): Exception while creating request: %s\n' % (url, str(e)))
			raise e

		try:
			result = handle.read()
		except Exception, e:
			self.log('get(%s): Exception while reading response: %s\n' % (url, str(e)))
			raise e
		
		return result

	def post(self, url, postdata=None, headers={}):
		""" 
			Returns result of a POST request.
		"""
		result = ''
		if postdata == None:
			encoded_data = ''
		elif type(postdata) == dict:
			encoded_data = urllib.urlencode(postdata)
		elif type(postdata) == str:
			encoded_data = postdata
		headers = dict(headers.items() + self.get_headers().items())
		try:
			req = self.Request(url, encoded_data, headers)
			handle = self.urlopen(req)
			result = handle.read()
		except Exception, e:
			self.log('post(%s): Exception: %s\n' % (url, str(e)))
			raise e
		return result

	def download(self, url, save_as):
		"""
			Downloads a file from 'url' and saves the file locally as 'save_as'.
		"""
		output = open(save_as, 'wb')
		
		req = urllib2.Request(url, headers=self.get_headers())
		file_on_web = self.urlopen(req)
		while True:
			buf = file_on_web.read(65536)
			if len(buf) == 0:
				break
			output.write(buf)
		output.close()

	def clear_cookies(self):
		""" Clears cookies in cookie jar.  """
		self.cj.clear()
	
	
	def set_user_agent(user_agent):
		""" Changes the user-agent used when connecting.  """
		self.user_agent = user_agent
	
	
	def between(self, source, start, finish):
		"""
			Helper method. Useful when parsing responses from web servers.
			
			Looks through a given source string for all items between two other strings, 
			returns the list of items (or empty list if none are found).
			
			Example:
				test = 'hello >30< test >20< asdf >>10<< sadf>'
				print between(test, '>', '<')
				
			would print the list:
				['30', '20', '>10']
		"""
		result = []
		i = source.find(start)
		j = source.find(finish, i + len(start))
		
		while i >= 0 and j >= 0:
			i = i + len(start)
			result.append(source[i:j])
			i = source.find(start, j + len(finish))
			j = source.find(finish, i + len(start))
		
		return result

	def get_extended(self, url, headers={}, retry=1):
		"""
			Attempts GET request with extended options
			Returns html source of a webpage (string)
			Follows redirects for 'retry' times
			Does *NOT* utilize cookie jar!
		"""
		if not 'User-agent' in headers:
			headers['User-agent'] = self.user_agent
		
		(https, host, path) = self.get_https_host_path(url)
		try:
			# Build and make request
			if https:
				req = httplib.HTTPSConnection(host)
			else:
				req = httplib.HTTPConnection(host)
			req.putrequest('GET', path)
			for hkey in headers.keys():
				req.putheader(hkey, headers[hkey])
			req.endheaders()

			resp = req.getresponse()

			# Request was successful, get response
			if resp.status == 200:
				return resp.read()
			# Redirect, follow it.
			elif resp.status in [301, 302] and resp.getheader('Location') != None:
				return self.get_extended(resp.getheader('Location'), headers=headers, retry=retry-1)

			# Don't retry 404 errors
			elif resp.status == 404:
				raise Exception('404 error')

			# Try to read response anyway, raise exception if needed
			else:
				result = resp.read()

		except Exception, e:
			# Don't bother retrying 404 errors
			if '404' in str(e):
				raise Exception(e)
			# Try again
			if retry > 0:
				return self.get_extended(url, headers=headers, retry=retry-1)
			raise Exception(e)
		raise Exception('status: %s - failed to get content at %s' % (resp.status, url))

	def get_https_host_path(self, url):
		"""
			Helper method used by get_extended()
			Args:
				url: URL to split into HTTPS, hostname, and file path
			Returns:
				Tuple:
					[0] "https": boolean, true if url is HTTPS, false otherwise
					[1] "host": Hostname from url
					[2] "path": Path from url
		"""
		https  = url.startswith('https')
		fields = url[url.find('//')+2:].split('/')
		host = fields[0]
		path = '/%s' % '/'.join(fields[1:])
		return (https, host, path)
	
if __name__ == '__main__':
	httpy = Httpy()
	url = 'http://www.example.com'
	r = httpy.get(url)
	httpy.log('get:    %s' % url)
	httpy.log('length: %d' % len(r))
	httpy.log('blurb:  %s' % r[0:50].replace('\n', ''))
	#r = httpy.post('http://requestb.in/xssxqyxs', {'key1' : 'value1'})
	#httpy.log('post:   %s' % url)
	#httpy.log('result: %s' % r)

