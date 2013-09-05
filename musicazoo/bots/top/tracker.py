#!/usr/bin/python

import mzbot
import time
import sqlite3

class TrackerBot(mzbot.MZBot):
	def __init__(self,url):
		self.luid=None
		mzbot.MZBot.__init__(self,url)

	def poll(self):
		req={'cmd':'cur','args':{'parameters':{'youtube':['url']}}}
		result=self.doCommands([req])
		self.assert_success(result)
		result=result[0]
		if 'result' in result and result['result']['type']=='youtube':
			uid=result['result']['uid']
			if uid != self.luid:
				url=result['result']['parameters']['url']
				self.got(url)
				self.luid=uid
		else:
			self.luid=None

	def got(self,url):
		conn=sqlite3.connect('mz.db')
		c=conn.cursor()
		c.execute('INSERT INTO youtube_history (url) VALUES (?)',[url])
		conn.commit()
		conn.close()

if __name__ == "__main__":
	tb = TrackerBot("http://ericserv.mit.edu/musicazoo/cmd")
	while True:
		tb.poll()
		time.sleep(1)
