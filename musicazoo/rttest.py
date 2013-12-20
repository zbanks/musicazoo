#!/usr/bin/python
import faulthandler
import hashlib
import hmac
import json
import time

import musicazoo.settings as settings

from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn

from musicazoo.backgroundmanager import BackgroundManager
from musicazoo.modulemanager import ModuleManager
from musicazoo.mzqueue import MZQueue, MZQueueManager
from musicazoo.staticmanager import StaticManager

HOST_NAME = ''
PORT_NUMBER = 9000

mm=ModuleManager(settings.MODULES)
sm=StaticManager(settings.STATICS)
bm=BackgroundManager(settings.BACKGROUNDS)

q = MZQueue(mm,sm,bm)
qm = MZQueueManager(q)
qm.start()

def spin(cmd,secs,freq):
	for i in range(secs*freq):
		print q.doCommand(cmd)
		time.sleep(1.0/freq)


test='''
Your've raised an interesting topic.  Before I can respond, I need to
replace your frequently used the term "open source", because I think
that is not a good choice of classification, because of the underlying
assumptions in it.  "Open source" refers to free/libre/swatantra
software but in a superficial practical way while avoiding the issues
of freedom.  (See http://thebaffler.com/past/the_meme_hustler for more
explanation.)

Since I think the freedom issues are centraly, I will use the term
"free software" and shun "open source".
'''

#q.doCommand({'cmd':'static_capabilities'})
#q.doCommand({'cmd':'statics','args':{'parameters':{1:['name','location']}}})
#q.doCommand({'cmd':'set_bg','args':{'type':'logo'}})
#spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},30,2)
#print q.doCommand({'cmd':'background_capabilities'})
#print q.doCommand({'cmd':'set_bg','args':{'type':'image','args':{'image':'http://www.changethethought.com/wp-content/tumblr_ljm3m8dfun1qzt4vjo1_500.gif'}}})
#spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},30,2)
#print q.doCommand({'cmd':'add','args':{'type':'text','args':{'text':'hello','speed':1.0,'duration':0}}})
#print q.doCommand({'cmd':'add','args':{'type':'text','args':{'text':test,'duration':3,'speed':1.3,'text_preprocessor':'remove_urls'}}})
#spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},5,2)
#print q.doCommand({'cmd':'add','args':{'type':'youtube','args':{'url':'http://www.youtube.com/watch?v=F57P9C4SAW4'}}})

#spin({'cmd':'cur','args':{'parameters':{'text':['status','text'],'youtube':['status']}}},2,2)

#print q.doCommand({'cmd':'tell_module','args':{'uid':0,'cmd':'stop'}})
#spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},15,2)
#print q.doCommand({'cmd':'tell_module','args':{'uid':0,'cmd':'seek_abs','args':{'position':3}}})
#spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},15,2)
#spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},15,2)

print "Please start"
q.doCommand({'cmd':'add', 'args':{'type': 'btc'}})
spin({'cmd':'cur', 'args':{'parameters':{}}}, 3, 1)
print "Please stop"
q.doCommand({'cmd':'tell_module', 'args':{'uid': '0', 'cmd':'stop'}})
spin({'cmd':'cur', 'args':{'parameters':{}}}, 3, 1)

