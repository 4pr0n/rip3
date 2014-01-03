#!/usr/bin/python

'''
	For checking the status of the rippers
	Can output the status to an HTML file to be ready by users
'''

from SiteBase import SiteBase
from DB import DB

from calendar import timegm
from time     import gmtime
from shutil   import move

SECONDS_BETWEEN_CHECKS = 3600
FILE_TO_WRITE = '../status.html'

class StatusManager(object):
	def __init__(self):
		self.db = DB()
		pass

	def execute(self):
		# Get existing statuses
		now = timegm(gmtime())
		cursor = self.db.conn.cursor()
		curexec = cursor.execute('select host, checked, available, message from sites')
		stored = curexec.fetchall()
		cursor.close()

		html_output = ''
		# Iterate over rippers, store new values for DB in 'insertmany'
		insertmany = []
		rippers = list(SiteBase.iter_rippers())
		if len(rippers) % 3 != 0:
			rippers = rippers[0:-(len(rippers) % 3)]
		for (index, ripper) in enumerate(rippers):
			host = ripper.get_host()
			url = ripper.get_sample_url()

			need_to_test = True
			# Find previous status / info
			oldhost = oldchecked = oldavailable = oldmessage = None
			for (oldhost, oldchecked, oldavailable, oldmessage) in stored:
				if oldhost == host:
					if now - oldchecked > SECONDS_BETWEEN_CHECKS:
						need_to_test = False
						break

			if need_to_test:
				checked = now
				try:
					print 'testing %s ripper...' % host
					result = ripper.test()
					'''
					# For testing the UI
					if index % 3 == 0:
						result = None
					elif index % 3 == 1:
						result = 'this site does not work right'
					else:
						raise Exception('this ripper REALLY does not work right')
					'''
					# test():
					# 1. Throws exception if something really bad happens (can't access site)
					# 2. Returns error message (str) if album output isn't as expected
					# 3. Returns None if it works as expected
					available = int(result == None)
					message = result
				except Exception, e:
					available = -1
					message = str(e)
				insertmany.append( (host, available, message, checked) )
			else:
				available = oldavailable
				message = oldmessage
				checked = oldchecked
			print host, url, available, message, checked
			html_output += self.host_html(host, url, available, message, checked)

		# Store any changes in the DB
		if len(insertmany) > 0:
			cursor = self.db.conn.cursor()
			curexec = cursor.executemany('insert or replace into sites values (?, ?, ?, ?)', insertmany)
			self.db.commit()
			cursor.close()
			
		# Write changes to HTML file
		temp_file = '%s.tmp' % FILE_TO_WRITE
		f = open(temp_file, 'w')
		f.write(html_output)
		f.flush()
		f.close()
		move(temp_file, FILE_TO_WRITE)
	
	def host_html(self, host, url, available, message, checked):
		if available == 1:
			color = 'success'
		elif available == 0:
			color = 'warning'
			sign = 'info'
		else: 
			color = 'danger'
			sign = 'exclamation'

		html  = '\n'
		html += '<div class="col-xs-6 col-sm-3 col-md-2 alert alert-%s" id="site_%s_div">\n' % (color, host)
		if available == 1:
			# Success, link to rip URL
			html += '  <button type="button" class="btn btn-success" onclick="window.location.hash = \'%s\'">\n' % url.replace('http://', '')
			html += '    %s <span class="glyphicon glyphicon-new-window"><span>\n' % host
			html += '  </button>\n'
		else:
			# Warning or danger, ripper isn't working as expected
			html += '  <button type="button" class="btn btn-%s" onclick="$(\'#site_%s\').slideToggle(200)">\n' % (color, host)
			html += '    %s <span class="glyphicon glyphicon-%s-sign"><span>\n' % (host, sign)
			html += '  </button>\n'
			html += '  <div id="site_%s" class="alert alert-%s" style="color: #fff; display: none; position: absolute; z-index: 99">%s</div>\n' % (host, color, message)
		html += '</div>\n'
		return html

if __name__ == '__main__':
	sm = StatusManager()
	sm.execute()
	#print sm.host_html('imagefap', 'asdf.com', 1, None, 5)
