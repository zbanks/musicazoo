#!/usr/bin/python

import BaseHTTPServer
import cgi
import faulthandler
import json
import os
import re
import tempfile
import sqlite3
import youtube_dl

HOST_NAME = ''
PORT_NUMBER = 9002

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

def get_yt(url):
	# General configuration
	#tf=tempfile.NamedTemporaryFile(delete=False)
	#tf.close()
	#proxies = compat_urllib_request.getproxies()
	#proxy_handler = compat_urllib_request.ProxyHandler(proxies)
	#https_handler = make_HTTPS_handler(None)
	#opener = compat_urllib_request.build_opener(https_handler, proxy_handler, cookie_processor, YoutubeDLHandler())
	#compat_urllib_request.install_opener(opener)

	y=youtube_dl.YoutubeDL({'outtmpl':'','format':'18'}) # empty outtmpl needed due to weird issue in youtube-dl
	y.add_default_info_extractors()

	try:
		info=y.extract_info(url,download=False)
	except Exception:
		return None

	return info['entries'][0]

yt_cache={}

class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
	pass

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def content_length(self,f):
		l=os.fstat(f.fileno()).st_size
		self.send_header("Content-length",str(l))

	def chunked_write(self,fr,to,chunksize=4096):
		while True:
			chunk=fr.read(chunksize)
			if not chunk:
				break
			to.write(chunk)

	def address_string(self):
		return str(self.client_address[0])

	def do_HEAD(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def do_GET(self):
		if self.path == '/':
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(
'''
<html>
<head>
<title>Tetazoo\'s Music Tastes</title>
</head>
<body>
''')
			self.wfile.write(self.makelist().encode('UTF8'))
			self.wfile.write(
'''
</body>
</html>
''')
			return

		self.send_error(404,'Bad request.')

	def makelist(self):
		global yt_cache
		self.db='/home/musicazoo/musicazoo/musicazoo/bots/top/mz.db'
		out=u'<ol>\n'
		conn=sqlite3.connect(self.db)
		c=conn.cursor()
		c.execute('SELECT COUNT(*) as num,url FROM youtube_history GROUP BY url ORDER BY num DESC LIMIT 30')
		while True:
			line=c.fetchone()
			if not line:
				break
			(count,url)=line
			if url not in yt_cache:
				info=get_yt(url)
				if 'title' in info:
					yt_cache[url]=u'<a href="{0}">{1}</a> ({2})'.format(url,info['title'],count)
				else:
					yt_cache[url]=u'<a href="{0}">{0}</a> ({1})'.format(url,count)
			out+=u'\t<li>{0}</li>\n'.format(yt_cache[url])
		conn.commit()
		conn.close()
		out+=u'</ol>\n'
		return out

if __name__ == '__main__':
	server_class = MultiThreadedHTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
	faulthandler.enable()
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

