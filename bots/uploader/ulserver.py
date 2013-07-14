#!/usr/bin/python

import BaseHTTPServer
import cgi
from upload_manager import UploadManager
import re
import tempfile
import os

HOST_NAME = ''
PORT_NUMBER = 9001

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
			infile=open('upload.html')
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
			f=uploader.get(uid)
			if f:
				infile=open(f.tempfilename)
				self.send_response(200)
				self.send_header("Content-type",f.mime_type)
				self.content_length(infile)
				self.end_headers()
				self.chunked_write(infile,self.wfile)
				infile.close()
			else:
				self.send_error(404,'Media not found: '+str(uid))
			return

		self.send_error(404,'Bad request.')

	def do_POST(self):
		try:
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))     
			if ctype == 'multipart/form-data':
				fs = cgi.FieldStorage( fp = self.rfile, 
					headers = self.headers, # headers_, 
					environ={ 'REQUEST_METHOD':'POST' } # all the rest will come from the 'headers' object,     
					# but as the FieldStorage object was designed for CGI, absense of 'POST' value in environ     
					# will prevent the object from using the 'fp' argument !     
				)

			else:
				raise Exception("Unexpected POST request")

			fs_up = fs['upfile']
			if not fs_up.filename:
				self.send_error(500,'No file sent.')
				return
			tf=tempfile.NamedTemporaryFile(delete=False)
			self.chunked_write(fs_up.file,tf)
			fs_up.file.close()
			tf.close()

			uploader.add(tf.name,nicefilename = os.path.split(fs_up.filename)[1])
			infile=open('success.html')
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.content_length(infile)
			self.end_headers()
			self.chunked_write(infile,self.wfile)
			infile.close()
			return

		except Exception as e:
			self.send_error(500,str(e))
			raise

	# End class ULHandler

uploader=UploadManager(('192.168.0.7',9001,''),('192.168.0.10',80,'cmd'))

if __name__ == '__main__':
	server_class = MultiThreadedHTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), ULHandler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

