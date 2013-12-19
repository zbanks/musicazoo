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
	pretty_params={'parameters':{'youtube':['title'],'netvid':['short_description'],'text':['short_description']}}

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
		if form_data is not None and 'q' in form_data:
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

	def pretty(self,mod):
		t=mod['type']
		if t=='youtube':
			return '"{0}"'.format(mod['parameters']['title'])
		if t=='netvid':
			return '{0}'.format(mod['parameters']['short_description'])
		if t=='text':
			return '{0}'.format(mod['parameters']['short_description'])
		return t

	def get_cur(self,params=pretty_params):
		return self.assert_success(self.doCommand({
			'cmd':'cur',
			'args':params
		}))

	def get_queue(self,params=pretty_params):
		return self.assert_success(self.doCommand({
			'cmd':'queue',
			'args':params
		}))

	def cmd_stop(self,q):
		def easy_stop(uid):
			self.assert_success(self.doCommand({'cmd':'tell_module','args':{'uid':uid,'cmd':'stop'}}))

		cur=self.get_cur()
		if cur is None:
			return 'Nothing to remove!'

		uid=cur['uid']
		t=cur['type']
		if t in ('youtube','netvid','text'):
			easy_stop(uid)
			return 'Removed {0}'.format(self.pretty(cur))
		raise Exception('Don\'t know how to stop {0}'.format(self.pretty(cur)))

	def cmd_pop(self, q):
		q=self.get_queue()
		if len(q)==0:
			if self.get_cur({}) is not None:
				return "Nothing on the queue! To stop the current video, use STOP"
			return 'Nothing on the queue!'
		last=q[-1]
		self.assert_success(self.doCommand({'cmd':'rm','args':{'uids':[last['uid']]}}))
		return 'Removed {0}'.format(self.pretty(last))

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

	def cmd_cur(self,q):
		cur=self.get_cur()
		if cur is None:
			return 'Nothing playing!'
		return 'Now Playing: {0}'.format(self.pretty(cur))

	def cmd_queue(self,q):
		queue=self.get_queue()
		if len(queue)==0:
			return 'Queue is empty!'
		return '\n'.join(['{0}. {1}'.format(n+1,self.pretty(q)) for (n,q) in zip(range(len(queue)),queue)])

	def cmd_help(self,q):
		return """Commands I understand:
help|? - This
vol [num] - Set volume
text|say [text] - Say something
stop|stfu|skip|next - Stop the current video
pop|undo|oops - Remove the last video on the queue
cur - Show what is currently playing
q|queue - List the queue
Anything else - Queue Youtube video
"""

	COMMANDS=(
		(r'^help$',cmd_help),
		(r'^$',cmd_help),
		(r'^\?$',cmd_help),
		(r'^vol (\d+)$',cmd_vol),
		(r'^text (.+)$',cmd_text),
		(r'^say (.+)$',cmd_text),
		(r'^stop$',cmd_stop),
		(r'^stfu$',cmd_stop),
		(r'^skip$',cmd_stop),
		(r'^next$',cmd_stop),
		(r'^pop$',cmd_pop),
		(r'^undo$',cmd_pop),
		(r'^oops$',cmd_pop),
		(r'^cur$',cmd_cur),
		(r'^q$',cmd_queue),
		(r'^queue$',cmd_queue),
		(r'^(.+)$',cmd_yt),
	)

if __name__=='__main__':
	NLPBot().run()
