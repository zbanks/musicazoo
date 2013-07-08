#!/usr/bin/python

import BaseHTTPServer
import queue
import cgi
import json

HOST_NAME = ''
PORT_NUMBER = 9000

from modulemanager import *
from staticmanager import *

import modules.youtube
import modules.text
import statics.volume

mm=ModuleManager([modules.youtube.Youtube,modules.text.Text])
sm=StaticManager([statics.volume.Volume()])

q=queue.MZQueue(mm,sm)
qm=queue.MZQueueManager(q)
qm.start()

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
	pass

class MZHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def address_string(self):
		return str(self.client_address[0])

	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Content-type", "text/json")
		s.end_headers()

	def do_GET(s):
		#s.giveError("Please POST a command.")
		s.send_response(200)
		s.send_header("Content-type", "text/html")
		s.send_header("Access-Control-Allow-Origin", "*")
#s.send_header("Access-Control-Allow-Headers", s.headers.getheader("Access-Control-Request-Headers"))
		s.end_headers()
		try:
			print s.path
			f = open(s.path[1:])
			s.wfile.write(f.read())
			f.close()
		except IOError:
			pass

	def giveError(s,error):
		s.send_response(200)
		s.send_header("Content-type", "text/json")
		s.end_headers()
		s.wfile.write(queue.errorPacket(error))

	def do_POST(s):
		"""
		ctype, pdict = cgi.parse_header(s.headers.getheader('content-type'))
		if ctype != 'text/json':
			s.giveError("No text/json found.")
			return
		"""
		
		length = int(s.headers.getheader('content-length'))
		postdata = s.rfile.read(length)
		try:
			parsedata=json.loads(postdata)
		except ValueError:
			s.giveError('Invalid JSON')
			return
		if not isinstance(parsedata,list):
			s.giveError('Input must be a list of commands.')
			return

		results=q.doMultipleCommandsAsync(parsedata)
		json_output=json.dumps(results)

		s.send_response(200)
		s.send_header("Access-Control-Allow-Origin", "http://localhost:8080")
		s.send_header("Content-type", "text/json")
		s.send_header("Access-Control-Allow-Headers", s.headers.getheader("Access-Control-Request-Headers"))
		s.end_headers()
		s.wfile.write(json_output)

if __name__ == '__main__':
	server_class = MultiThreadedHTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), MZHandler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

