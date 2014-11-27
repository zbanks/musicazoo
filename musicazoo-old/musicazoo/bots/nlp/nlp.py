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
    pretty_params={'parameters':{'youtube':['title','duration','time'],'netvid':['short_description'],'text':['short_description']}}

    def __init__(self):
        Webserver.__init__(self,HOST_NAME,PORT_NUMBER)
        MZBot.__init__(self,MZQ_URL)

    def json_transaction(self,json):
        try:
            if 'incomplete' in json and json['incomplete']:
                result=self.complete(json['q'])
            result=self.act(json['q'])
            return {'success':True,'result':result}
        except Exception as e:
            return {'success':False,'error':str(e)}

    def html_transaction(self,form_data):
        if form_data is not None and 'q' in form_data:
            try:
                if 'incomplete' in form_data:
                    return '\n'.join(self.complete(form_data['q']))
                return self.act(form_data['q'])
            except Exception as e:
                return "Error!\n"+str(e)
        else:
            return "<form method='POST'><input name='q'></input><input type='submit'></form><form method='POST'><input name='q'></input><input type='submit' value='Complete'><input type='hidden' name='incomplete'></input></form>"

    def act(self,q):
        q=q.strip()
        for (regex,func) in self.COMMANDS:
            m=re.match(regex,q,re.I)
            if m:
                return func(self,q,*m.groups())
                break
        raise Exception("Command not recognized.")

    def complete(self,q):
        q=q.strip()
        return [q+' porn',q+' creepy porn',q+' weird porn']

    def cmd_set_vol(self,q,vol):
        scap=self.assert_success(self.doCommand({'cmd':'static_capabilities'}))
        vol_i=None
        for (i,static) in scap.iteritems():
            if static['class']=='volume':
                vol_i=i
                break
        if not vol_i:
            raise Exception("Volume static not found.")

        if vol=='up':
            result=self.assert_success(self.doCommand({"cmd":"statics","args":{"parameters":{str(vol_i):["vol"]}}}))
            vol=max(result[str(vol_i)]['vol']+5,0)
        elif vol=='down':
            result=self.assert_success(self.doCommand({"cmd":"statics","args":{"parameters":{str(vol_i):["vol"]}}}))
            vol=min(result[str(vol_i)]['vol']-5,100)
        else:
            vol=int(vol)

        if vol>100:
            raise Exception("Volume cannot be greater than 100")
        self.assert_success(self.doCommand({
            "cmd": "tell_static", "args":
            {
                "uid": vol_i,
                "cmd": "set_vol",
                "args": {"vol": vol}
            }
        }))

        return "Volume set to {0}".format(vol)

    def cmd_get_vol(self,q):
        scap=self.assert_success(self.doCommand({'cmd':'static_capabilities'}))
        vol_i=None
        for (i,static) in scap.iteritems():
            if static['class']=='volume':
                vol_i=i
                break
        if not vol_i:
            raise Exception("Volume static not found.")
        result=self.assert_success(self.doCommand({"cmd":"statics","args":{"parameters":{str(vol_i):["vol"]}}}))
        v=result[str(vol_i)]['vol']
        return "Volume is {0}".format(v)

    def pretty(self,mod):
        t=mod['type']
        if t=='youtube':
            return u'"{0}"'.format(mod['parameters']['title'])
        if t=='netvid':
            return u'{0}'.format(mod['parameters']['short_description'])
        if t=='text':
            return u'{0}'.format(mod['parameters']['short_description'])
        return mod['parameters']['str']

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
        if t in ('youtube','netvid','text','btc'):
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
        return u'Queued "{0}"'.format(title)

    def cmd_cur(self,q):
        cur=self.get_cur()
        if cur is None:
            return 'Nothing playing!'
        if not ('duration' in cur['parameters'] and 'time' in cur['parameters']):
            return 'Now Playing: {0}'.format(self.pretty(cur))
        ratio = float(cur['parameters']['time']) / cur['parameters']['duration']
        size = 20 #Perhaps later make this duration-dependent.
        barlength = int(size * ratio)
        if barlength == 0:
            bar = " "*size
        elif barlength == 1:
            bar = "8" + " "*(size-1)
        elif barlength < .7*size:
            bar = "8" + "="*(barlength-2) + "D" + " "*(size-barlength)
        else:
            bar = "8" + "="*int(.7*size-2) + "D" + "~"*(barlength-int(.7*size)) + " "*(size-barlength)
        return u'Now Playing: {0}\n[{1}]'.format(self.pretty(cur),bar)

    def cmd_queue(self,q):
        queue=self.get_queue()
        if len(queue)==0:
            return 'Queue is empty!'
        return u'\n'.join([u'{0}. {1}'.format(n+1,self.pretty(q)) for (n,q) in zip(range(len(queue)),queue)])

    def cmd_btc(self,q):
        self.assert_success(self.doCommand({
            'cmd':'add',
            'args':
            {
                'type': 'btc',
                'args': {},
            }
        }))
        return "Here's how much money you lost."

    def cmd_help(self,q):
        return """Commands I understand:
help|? - This
vol - Get volume
vol [num] - Set volume
vol up|down - Change volume
text|say [text] - Say something
stop|stfu|skip|next - Stop the current video
pop|undo|oops - Remove the last video on the queue
cur - Show what is currently playing
q|queue - List the queue
btc - List BTC prices
Anything else - Queue Youtube video
"""

    COMMANDS=(
        (r'^help$',cmd_help),
        (r'^$',cmd_help),
        (r'^\?$',cmd_help),
        (r'^vol (\d+|up|down)$',cmd_set_vol),
        (r'^vol$',cmd_get_vol),
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
        (r'^btc$',cmd_btc),
        (r'^rm$',lambda x,y:"rm is ambiguous. Use stop or pop."),
        (r'^(.+)$',cmd_yt),
    )

if __name__=='__main__':
    NLPBot().run()
