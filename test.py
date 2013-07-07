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
print q.doCommand({'cmd':'add','args':['youtube','asdf']})
print q.doCommand({'cmd':'queue','args':[{'youtub':['url']}]})
print q.doCommand({'cmd':'queue','args':[{'youtube':['url']}]})
q.next()
print q.doCommand({'cmd':'cur','args':[{'youtube':['url']}]})
print q.doCommand({'cmd':'tell_module','args':[0,'pause']})
print q.doCommand({'cmd':'tell_static','args':[0,'set_vol',100]})
