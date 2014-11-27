#!/usr/bin/python

from mzbot import MZBot
import BaseHTTPServer
import SocketServer
import mimetypes
import threading
import time
import sys
import os
import re

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
			time.sleep(1)
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

	class MultiThreadedHTTPServer(SocketServer.ThreadingMixIn,BaseHTTPServer.HTTPServer):
	#class MultiThreadedHTTPServer(BaseHTTPServer.HTTPServer):
		pass

	class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
		def address_string(self):
			return str(self.client_address[0])

		def chunked_write(self,fr,to,length,chunksize=4096):
			total=0
			while True:
				chunk=fr.read(min(chunksize,total-length))
				total+=len(chunk)
				to.write(chunk)
				if total==length:
					break

		def parse_range(self):
			if 'range' not in self.headers:
				return (None,None)
			r=re.match(r'^(?:bytes=)?(\d+)-(\d*)$',self.headers['range'])
			if r is None:
				return (None,None)
			start=int(r.group(1))
			stop=r.group(2)
			if stop=='':
				stop=None
			else:
				stop=int(stop)
			return (start,stop)

		def do_GET(self):
			self.do_GETHEAD(True)

		def do_GETHEAD(self,content):
			infile=open(self.server.file_to_host,'rb')
			fl=os.fstat(infile.fileno()).st_size
			(start,stop)=self.parse_range()

			if start==None:
				self.send_response(200)
			elif start>=fl or stop>=fl:
				self.send_error(416)
			else:
				if stop is None:
					stop=fl-1
				self.send_response(206)
				self.send_header("Content-range","bytes {0}-{1}/{2}".format(start,stop,fl))

			if start is None:
				start=0
			if stop is None:
				stop=fl-1

			self.send_header("Content-type", mimetypes.guess_type(self.server.file_to_host)[0])
			self.send_header("Content-length",str(stop-start+1))
			self.send_header("Accept-Ranges","bytes")
			self.end_headers()
			if content:
				infile.seek(start,0)
				self.chunked_write(infile,self.wfile,stop-start+1)
			infile.close()
			return

		def do_HEAD(self):
			self.do_GETHEAD(False)

if __name__=='__main__':
	PusherBot(sys.argv[1],sys.argv[2]).push()
	#PusherBot("http://musicazoo.mit.edu/cmd","C:\Users\Public\Pictures\Sample Pictures\Chrysanthemum.jpg").push()

