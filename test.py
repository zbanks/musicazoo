#!/usr/bin/python

from queue import *
from vol import *

q=MZQueue([Volume()])
print q.doCommand({'cmd':'capabilities'})
print q.doCommand({'cmd':'statics'})
