#!/usr/bin/python

import json
import os
import re
import tempfile
import sqlite3
import requests

from musicazoo.lib.webserver import Webserver

HOST_NAME = ''
PORT_NUMBER = 9002

def get_info(vid):
	# Return the args dict for the first youtube result for 'match'
	youtube_req_url = "http://gdata.youtube.com/feeds/api/videos/{0}".format(vid)
	youtube_data = {
		"v": 2,
		"alt": "jsonc",
	}
	youtube_data = requests.get(youtube_req_url, params=youtube_data).json()

	if 'data' in youtube_data:
		return youtube_data['data']
	else:
		return {"title": "(Unknown: %s)" % vid, "url": vid}

yt_cache={}

class ViewerBot(Webserver):
	def __init__(self):
		Webserver.__init__(self,HOST_NAME,PORT_NUMBER)

	def json_transaction(self, json):
		if "limit" in json:
			limit = json["limit"]
		else:
			limit = 30
		return self.make_json_list(limit=limit)

	def html_transaction(self,form_data):
		try:
			n=int(form_data['n'])
			if n<0:
				raise ValueError
		except Exception:
			n=30

		out='''
<html>
<head>
<title>Tetazoo\'s Music Tastes</title>
</head>
<body>
'''
		out+=self.makelist(n).encode('UTF8')
		out+='''
</body>
</html>
'''
		return out

	def makelist(self,n=30):
		global yt_cache
		def format_yt_link(url, title=None):
			if title is not None:
				return u"<a href='{0}'>{1}</a>".format(url, title)
			return u"<a href='{0}'>{0}</a>".format(url, url)
		self.db=os.path.join(os.path.dirname(os.path.realpath(__file__)),'mz.db')
		out=u''
		conn=sqlite3.connect(self.db)
		c=conn.cursor()
		c.execute('SELECT COUNT(*) as num,url FROM youtube_history GROUP BY url ORDER BY num DESC, t DESC LIMIT {0}'.format(n))
		n=1
		last_n=1
		last_count=None
		while True:
			line=c.fetchone()
			if not line:
				break
			(count,vid)=line
			if vid not in yt_cache:
				info=get_info(vid)
				url="http://youtube.com/watch?v={0}".format(vid)
				if 'title' in info:
					yt_cache[vid]=(url,info['title'])
				else:
					yt_cache[vid]=(url)

			if count==last_count:
				n_to_show==last_n
			else:
				n_to_show=n
				last_count=count
			n+=1

			out+=u'\t<p>{0}. {1} ({2})</p>\n'.format(n_to_show,format_yt_link(*yt_cache[vid]),count)
		conn.commit()
		conn.close()
		return out

	def make_json_list(self, limit=30):
		global yt_cache
		self.db=os.path.join(os.path.dirname(os.path.realpath(__file__)),'mz.db')
		out=u''
		conn=sqlite3.connect(self.db)
		c=conn.cursor()
		c.execute('SELECT COUNT(*) as num,url FROM youtube_history GROUP BY url ORDER BY num DESC, t DESC LIMIT {0}'.format(limit))
		n=1
		last_n=1
		last_count=None
		result = []
		while True:
			line=c.fetchone()
			if not line:
				break
			(count,vid)=line
			if vid not in yt_cache:
				info=get_info(vid)
				url="http://youtube.com/watch?v={0}".format(vid)
				if 'title' in info:
					yt_cache[vid]=(url,info['title'])
				else:
					yt_cache[vid]=(url)

			if count==last_count:
				n_to_show==last_n
			else:
				n_to_show=n
				last_count=count
			n+=1

			result.append({"n": n_to_show, "url": yt_cache[vid][0], "title": yt_cache[vid][1], "count": count})

#out+=u'\t<p>{0}. {1} ({2})</p>\n'.format(n_to_show,yt_cache[vid],count)
		conn.commit()
		conn.close()
		return result

if __name__=='__main__':
	ViewerBot().run()

