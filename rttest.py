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


print q.doCommand({'cmd':'add','args':{'type':'text','args':{'text':'hello i am a text','duration':3}}})

spin({'cmd':'cur','args':{'parameters':{'text':['status','text']}}},200,2)
