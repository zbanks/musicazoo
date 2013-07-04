#!/usr/bin/python

import BaseHTTPServer
import queue
import cgi
import json

HOST_NAME = ''
PORT_NUMBER = 9000

import vol

q=queue.MZQueue([vol.VolumeModule()])

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Content-type", "text/json")
		s.end_headers()

	def do_GET(s):
		s.giveError("Please POST a command.")

	def giveError(s,error):
		s.send_response(200)
		s.send_header("Content-type", "text/json")
		s.end_headers()
		s.wfile.write(queue.errorPacket(error))

	def do_POST(s):
		ctype, pdict = cgi.parse_header(s.headers.getheader('content-type'))
		if ctype != 'text/json':
			s.giveError("No text/json found.")
			return
		
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

		results=[q.doCommand(cmd) for cmd in parsedata]
		json_output=json.dumps(results)

		s.send_response(200)
		s.send_header("Content-type", "text/json")
		s.end_headers()
		s.wfile.write(json_output)

if __name__ == '__main__':
	server_class = BaseHTTPServer.HTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

