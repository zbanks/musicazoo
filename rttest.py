#!/usr/bin/python

import time
from queue import *
from statics.volume import *
from modules.youtube import *
from modules.text import *
from modulemanager import *
from staticmanager import *

mm=ModuleManager([Youtube,Text])
sm=StaticManager([Volume()])

q=MZQueue(mm,sm)
qm=MZQueueManager(q)
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

print q.doCommand({'cmd':'add','args':{'type':'text','args':{'text':test,'duration':3,'speed':1.3}}})
#print q.doCommand({'cmd':'add','args':{'type':'youtube','args':{'url':'http://www.youtube.com/watch?v=F57P9C4SAW4'}}})

spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},150,2)
#print q.doCommand({'cmd':'tell_module','args':{'uid':0,'cmd':'set_rate','args':{'rate':0.5}}})
#spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},15,2)
