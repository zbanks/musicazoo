#!/usr/bin/python

from musicazoo.lib.mzbot import MZBot
import time
import sqlite3
import os
import re

class TrackerBot(MZBot):
	def __init__(self,url):
		self.luid=None
		self.db=os.path.join(os.path.dirname(os.path.realpath(__file__)),'mz.db')
		MZBot.__init__(self,url)

	def poll(self):
		req={'cmd':'cur','args':{'parameters':{'youtube':['url']}}}
		result=self.assert_success(self.doCommand(req))
		if result and result['type']=='youtube':
			uid=result['uid']
			if uid != self.luid:
				url=result['parameters']['url']
				v=re.search(r'watch\?v=(.+)$',url)
				if v:
					self.got(v.group(1))
				self.luid=uid
		else:
			self.luid=None

	def got(self,url):
		print "GOT",url
		conn=sqlite3.connect(self.db)
		c=conn.cursor()
		c.execute('INSERT INTO youtube_history (url) VALUES (?)',[url])
		conn.commit()
		conn.close()

if __name__ == "__main__":
	tb = TrackerBot("http://musicazoo.mit.edu/cmd")
	while True:
		time.sleep(3)
		tb.poll()
