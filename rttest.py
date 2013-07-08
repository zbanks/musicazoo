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


#print q.doCommand({'cmd':'add','args':{'type':'text','args':{'text':'hello i am a long text that should totally wrap around the screen a few times','duration':3}}})
print q.doCommand({'cmd':'add','args':{'type':'youtube','args':{'url':'http://www.youtube.com/watch?v=F57P9C4SAW4'}}})

spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},200,2)
#print q.doCommand({'cmd':'tell_module','args':{'uid':0,'cmd':'stop'}})
