#!/usr/bin/python

import time
from queue import *
from statics.volume import *
from modules.youtube import *
from modulemanager import *
from staticmanager import *

mm=ModuleManager([Youtube])
sm=StaticManager([Volume()])

q=MZQueue(mm,sm)
qm=MZQueueManager(q)
qm.start()

def spin(cmd,secs,freq):
	for i in range(secs*freq):
		print q.doCommand(cmd)
		time.sleep(1.0/freq)


print q.doCommand({'cmd':'add','args':{'type':'youtube','args':{'url':'http://www.youtube.com/watch?v=F57P9C4SAW4'}}})
#print q.doCommand({'cmd':'add','args':{'type':'youtube','args':{'url':'http://vimeo.com/69668299'}}})

#print q.doCommand({'cmd':'add','args':{'type':'youtube','args':{'url':'asdf'}}})

spin({'cmd':'cur','args':{'parameters':{'youtube':['status','duration','time']}}},40,2)
print q.doCommand({'cmd':'tell_module','args':{'uid':0,'cmd':'stop'}})
spin({'cmd':'cur','args':{'parameters':{'youtube':['status','duration','time']}}},5,2)
