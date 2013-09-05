#!/usr/bin/python

import BaseHTTPServer
import cgi
import faulthandler
import json
import os
import re
import tempfile
import sqlite3

HOST_NAME = ''
PORT_NUMBER = 9002

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
	pass

class ULHandler(BaseHTTPServer.BaseHTTPRequestHandler):

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
			self.wfile.write(self.makelist())
			self.wfile.write(
'''
</body>
</html>
''')
			return

		self.send_error(404,'Bad request.')

	def makelist(self):
		out='<ol>\n'
		conn=sqlite3.connect('mz.db')
		c=conn.cursor()
		c.execute('SELECT COUNT(*) as num,url FROM youtube_history GROUP BY url ORDER BY num')
		while True:
			line=c.fetchone()
			if not line:
				break
			out+='\t<li><a href=\'{1}\'>{1}</a> ({0})</li>\n'.format(*line)
		conn.commit()
		conn.close()
		out+='</ol>\n'
		return out
	

if __name__ == '__main__':
	server_class = MultiThreadedHTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), ULHandler)
	faulthandler.enable()
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

