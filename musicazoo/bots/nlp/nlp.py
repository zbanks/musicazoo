#!/usr/bin/env python

import BaseHTTPServer
import cgi
import json
import magic
import os
import urlparse
import requests
import re

HOST_NAME = ''
PORT_NUMBER = 9003

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

MZQ_URL='http://musicazoo.mit.edu/cmd'

class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
	pass

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def address_string(self):
		return str(self.client_address[0])

	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Content-type", "application/json")
		s.end_headers()

	def parse(self,q):
		g=r'vol (\d\d?\d?)'.match(q)
		if g:
			try:
				vol=int(g.group(1))
				if vol>100:
					raise Exception

			except:
				pass

	def do_GET(s):
		qd=urlparse.parse_qsl(urlparse.urlparse(s.path).query)
		if not qd:
			return
		q=dict(qd)['q']
		s.act(q)
		
	def do_POST(s):
		ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))	 
		if ctype == 'multipart/form-data':
			fs = cgi.FieldStorage( fp = self.rfile, 
				headers = self.headers, # headers_, 
				environ={ 'REQUEST_METHOD':'POST' } # all the rest will come from the 'headers' object,	 
				# but as the FieldStorage object was designed for CGI, absense of 'POST' value in environ	 
				# will prevent the object from using the 'fp' argument !	 
			)
		else:	
			raise Exception('Unexpected post request')

		q=fs['q'].value
		s.act(q)

	def act(s,q):
		try:
			commands=s.parse(q)
		except Exception as e:
			s.send_error(500,str(e))
			return
		s.send_response(200)
		s.send_header("Content-type", "application/json")
		s.end_headers()
		s.wfile.write(resp)

	def req(s,commands):
		return json.loads(requests.post(MZQ_URL, json.dumps(commands)).text)

if __name__ == '__main__':
	server_class = MultiThreadedHTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

