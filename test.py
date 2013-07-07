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
print q.doCommand({'cmd':'module_capabilities'})
print q.doCommand({'cmd':'static_capabilities'})
print q.doCommand({'cmd':'statics','args':{'parameters':{0:['vol']}}})
print q.doCommand({'cmd':'add','args':{'type':'youtube','args':{'url':'asdf'}}})
print q.doCommand({'cmd':'queue','args':{'parameters':{'youtub':['url']}}})
print q.doCommand({'cmd':'queue','args':{'parameters':{'youtube':['url']}}})
print q.doCommand({'cmd':'ask_module','args':{'uid':0,'parameters':['url']}})
q.next()
print q.doCommand({'cmd':'cur','args':{'parameters':{'youtube':['url']}}})
print q.doCommand({'cmd':'tell_module','args':{'uid':0,'cmd':'pause'}})
print q.doCommand({'cmd':'tell_static','args':{'uid':0,'cmd':'set_vol','args':{'vol':100}}})
