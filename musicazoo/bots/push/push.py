#!/usr/bin/python

from musicazoo.lib.mzbot import MZBot
import BaseHTTPServer
import os
import mimetypes
import httplib
import threading
import time

class PusherBot(MZBot,threading.Thread): # i am the pusher robot
	def __init__(self,mzq_url,file_to_host,host_name='',port_number=9100,vid_name=None):
		MZBot.__init__(self,mzq_url)
		threading.Thread.__init__(self)
		self.daemon=True

		self.port_number=port_number

		mimetypes.init()
		self.httpd = PusherBot.MultiThreadedHTTPServer((host_name,port_number), PusherBot.MyHandler)
		self.httpd.file_to_host = file_to_host
		if vid_name is None:
			self.vid_name = os.path.basename(file_to_host)
		else:
			self.vid_name=vid_name

	def push(self):
		self.my_ip=self.whoami()
		self.start()
		self.add()
		try:
			while True:
				time.sleep(3)
				if not self.still_playing():
					break
			time.sleep(3)
		except KeyboardInterrupt:
			self.remove()
		self.httpd.shutdown()
		self.join()

	def add(self):
		result=self.assert_success(self.doCommand({
			'cmd':'add',
			'args':{
				'type':'netvid',
				'args':{
					'url':'http://{0}:{1}'.format(self.my_ip,self.port_number),
					'short_description':self.vid_name
				}
			}
		}))
		self.added_uid=result['uid']

	def queue_plus_cur(self):
		results=self.assert_success(self.doCommands([
		{
			'cmd':'queue',
			'args':{'parameters':{}}
		},
		{
			'cmd':'cur',
			'args':{'parameters':{}}
		}
		]))
		if len(results)==1:
			return results[0]
		else:
			return results[0]+[results[1]]

	def still_playing(self):
		return self.added_uid in [mod['uid'] for mod in self.queue_plus_cur()]

	def remove(self):
		self.doCommands([
		{
			'cmd':'tell_module',
			'args':{
				'uid':self.added_uid,
				'cmd':'stop'
			}
		},
		{
			'cmd':'rm',
			'args':{
				'uids':[self.added_uid]
			}
		}
		])

	def run(self):
		self.httpd.serve_forever()
		self.httpd.server_close()

	#class MultiThreadedHTTPServer(ThreadingMixIn,BaseHTTPServer.HTTPServer): # No threading for testing
	class MultiThreadedHTTPServer(BaseHTTPServer.HTTPServer):
		pass

	class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
		def address_string(self):
			return str(self.client_address[0])

		def content_length(self,f):
			l=os.fstat(f.fileno()).st_size
			self.send_header("Content-length",str(l))

		def chunked_write(self,fr,to,chunksize=4096):
			while True:
				chunk=fr.read(chunksize)
				if not chunk:
					break
				to.write(chunk)

		def do_GET(self):
			infile=open(self.server.file_to_host)
			self.send_response(200)
			self.send_header("Content-type", mimetypes.guess_type(self.server.file_to_host)[0])
			self.content_length(infile)
			self.end_headers()
			self.chunked_write(infile,self.wfile)
			infile.close()
			return

		def do_HEAD(self):
			infile=open(self.server.file_to_host)
			self.send_response(200)
			self.send_header("Content-type", mimetypes.guess_type(self.server.file_to_host)[0])
			self.content_length(infile)
			self.end_headers()
			infile.close()

if __name__=='__main__':
	PusherBot('http://localhost:9000','chainsaw.avi').push()

