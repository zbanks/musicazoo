#!/usr/bin/python

import BaseHTTPServer
import cgi
import faulthandler
import json
import re
import os

from local_manager import LocalManager

HOST_NAME = ''
PORT_NUMBER = 9004

MYPATH=os.path.dirname(__file__)

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
	pass

class FileHandler(BaseHTTPServer.BaseHTTPRequestHandler):

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
			infile=open(os.path.join(MYPATH,'local.html'))
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.content_length(infile)
			self.end_headers()
			self.chunked_write(infile,self.wfile)
			infile.close()
			return

		result=re.match(r'/media/(\d+)',self.path)
		if result:
			uid=int(result.group(1))
			f=manager.get(uid)
			if f:
				infile=open(f.localfilename)
				self.send_response(200)
				self.send_header("Content-type",f.mime_type)
				self.content_length(infile)
				self.send_header("Content-disposition","attachment; filename="+f.nicefilename)
				self.end_headers()
				self.chunked_write(infile,self.wfile)
				infile.close()
			else:
				self.send_error(404,'Media not found: '+str(uid))
			return

		self.send_error(404,'Bad request.')

	def do_POST(self):	
		if self.path == '/':
			try:
				self.play_file()
			except Exception as e:
				self.send_error(500,str(e))
				return

			infile=open(os.path.join(MYPATH,'success.html'))
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.content_length(infile)
			self.end_headers()
			self.chunked_write(infile,self.wfile)
			infile.close()
		elif self.path=='/api':
			try:
				self.play_file()
			except Exception as e:
				self.send_response(200)
				self.send_header("Content-type", "text/json")
				self.end_headers()
				self.wfile.write(json.dumps({'success':False,'error':str(e)}))
				return

			self.send_response(200)
			self.send_header("Content-type", "text/json")
			self.end_headers()
			self.wfile.write(json.dumps({'success':True}))
		else:
			self.send_error(404,'Unexpected post request')


	def play_file(self):
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

		local_file=fs['localfile'].value
		manager.add(local_file,nicefilename = os.path.split(local_file)[-1])

	# End class FileHandler

manager=LocalManager('http://musicazoo.mit.edu/local','http://localhost/cmd')

if __name__ == '__main__':
	server_class = MultiThreadedHTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), FileHandler)
	faulthandler.enable()
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

