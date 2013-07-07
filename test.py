#!/usr/bin/python

import time
from queue import *
from statics.volume import *

q=MZQueue([Volume()])
print q.doCommand({'cmd':'capabilities'})
print q.doCommand({'cmd':'statics'})
print q.doCommand({'cmd':'add','args':['youtube','http://www.youtube.com/watch?v=F57P9C4SAW4']})
q.next()
print q.doCommand({'cmd':'cur','args':[{'youtub':['url','str']}]})
