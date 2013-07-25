#!/usr/bin/env python

import sys,os
mypath=os.path.dirname(__file__)
libpath=os.path.join(mypath,'lib/')
sys.path.append(libpath)

import loading
import time
import faulthandler

faulthandler.enable()

while True:
	l=loading.LoadingScreen()
	l.show()
	#time.sleep(.1)
	l.close()
	#time.sleep(.1)
