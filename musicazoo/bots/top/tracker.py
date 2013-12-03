#!/usr/bin/python

from musicazoo.lib.mzbot import MZBot
import time
import sqlite3

class TrackerBot(mzbot.MZBot):
	def __init__(self,url):
		self.luid=None
		self.db="/home/musicazoo/musicazoo/musicazoo/bots/top/mz.db"
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
