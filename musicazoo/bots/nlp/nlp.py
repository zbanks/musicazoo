#!/usr/bin/python

from musicazoo.lib.mzbot import MZBot
from musicazoo.lib.webserver import Webserver
import requests
import re

HOST_NAME = ''
PORT_NUMBER=9003
MZQ_URL='http://musicazoo.mit.edu/cmd'

def youtube_lucky_args(q):
	# Return the args dict for the first youtube result for 'match'
	youtube_req_url = "http://gdata.youtube.com/feeds/api/videos"
	youtube_data = {
		"v": 2,
		"orderby": "relevance",
		"alt": "jsonc",
		"q": q,
		"max-results": 5
	}
	youtube_data = requests.get(youtube_req_url, params=youtube_data).json()

	yi=youtube_data['data']['items']

	if len(yi)>0:
		return youtube_data["data"]["items"][0]
	else:
		return None

class NLPBot(MZBot,Webserver):
	def __init__(self):
		Webserver.__init__(self,HOST_NAME,PORT_NUMBER)
		MZBot.__init__(self,MZQ_URL)

	def json_transaction(self,json):
		try:
			result=self.act(json['q'])
			return {'success':True,'result':result}
		except Exception as e:
			return {'success':False,'error':str(e)}

	def html_transaction(self,form_data):
		if form_data and 'q' in form_data:
			try:
				return self.act(form_data['q'])
			except Exception as e:
				return "Error!\n"+str(e)
		else:
			return "<form method='POST'><input name='q'></input><input type='submit'></form>"

	def act(self,q):
		q=q.strip()
		for (regex,func) in self.COMMANDS:
			m=re.match(regex,q,re.I)
			if m:
				return func(self,q,*m.groups())
				break
		raise Exception("Command not recognized.")

	def cmd_vol(self,q,vol):
		vol=int(vol)
		if vol>100:
			raise Exception("Volume cannot be greater than 100")
		scap=self.assert_success(self.doCommand({'cmd':'static_capabilities'}))
		vol_i=None
		for (i,static) in scap.iteritems():
			if static['class']=='volume':
				vol_i=i
				break
		if not vol_i:
			raise Exception("Volume static not found.")
		self.assert_success(self.doCommand({
			"cmd": "tell_static", "args":
			{
				"uid": vol_i,
				"cmd": "set_vol",
				"args": {"vol": vol}
			}
		}))

		return "Volume set to {0}".format(vol)

	def cmd_rm(self,q):
		def easy_stop(uid):
			self.assert_success(self.doCommand({'cmd':'tell_module','args':{'uid':uid,'cmd':'stop'}}))

		cur=self.assert_success(self.doCommand({
			'cmd':'cur',
			'args':{'parameters':{'youtube':['title'],'netvid':['short_description'],'text':['short_description']}}
		}))
		t=cur['type']
		uid=cur['uid']
		if t=='youtube':
			easy_stop(uid)
			return 'Removed "{0}"'.format(cur['parameters']['title'])
		if t=='netvid':
			easy_stop(uid)
			return 'Removed "{0}"'.format(cur['parameters']['short_description'])
		if t=='text':
			easy_stop(uid)
			return 'Removed "{0}"'.format(cur['parameters']['short_description'])
		raise Exception('Don\'t know how to stop "{0}"'.format(t))

	def cmd_pop(self, q):
		raise NotImplementedError("Wishful thinking...")

	def cmd_text(self,q,text):
		self.assert_success(self.doCommand({
			'cmd':'add',
			'args':
			{
				'type': 'text',
				'args':
				{
					"text": text,
					"text_preprocessor": "none",
					"speech_preprocessor": "pronunciation",
					"text2speech": "google",
					"renderer": "splash",
					"duration": 1,
					"short_description": "(Text)",
					"long_description": "Text: %s" % text,
				}
			}
		}))
		return 'Queued text.'

	def cmd_yt(self,q,kw):
		res=youtube_lucky_args(kw)
		if not res:
			raise Exception('No Youtube results found.')
		title=res['title']
		url='http://youtube.com/watch?v={0}'.format(res['id'])

		self.assert_success(self.doCommand({
			'cmd':'add',
			'args': {
				'type': 'youtube',
				'args': {'url':url}
			}
		}))
		return 'Queued "{0}"'.format(title)

	COMMANDS=(
		(r'^vol (\d+)$',cmd_vol),
		(r'^text (.+)$',cmd_text),
		(r'^say (.+)$',cmd_text),
		(r'^rm$',cmd_rm),
		(r'^stfu$',cmd_rm),
		(r'^skip$',cmd_rm),
		(r'^next$',cmd_rm),
		(r'^pop$',cmd_pop),
		(r'^undo$',cmd_pop),
		(r'^(.+)$',cmd_yt),
	)

if __name__=='__main__':
	NLPBot().run()
