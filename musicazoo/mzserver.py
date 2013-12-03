#!/usr/bin/env python
import hashlib
import hmac
import json
import sys
import os

import musicazoo.settings as settings

from musicazoo.backgroundmanager import BackgroundManager
from musicazoo.modulemanager import ModuleManager
from musicazoo.mzqueue import MZQueue, MZQueueManager
from musicazoo.staticmanager import StaticManager

from musicazoo.lib.webserver import Webserver,HTTPException

HOST_NAME = ''
PORT_NUMBER = 9000

class MZServer(Webserver):
	def __init__(self,debug=False):
		self.debug=debug

		mm=ModuleManager(settings.MODULES)
		sm=StaticManager(settings.STATICS)
		bm=BackgroundManager(settings.BACKGROUNDS)

		self.q = MZQueue(mm,sm,bm)
		self.qm = MZQueueManager(self.q)
		self.qm.start()

		Webserver.__init__(self,HOST_NAME, PORT_NUMBER)

	def get(self,form_data,path):
		if self.debug:
			p=path.path
			if p=='/' or p=='':
				p='/index.html'
			try:
				fn=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../www',p[1:])
				return open(fn)
			except Exception:
				raise HTTPException(404,'File not found')
		else:
			raise NotImplementedError

	def json_transaction(self,json_data):
        	return self.q.doMultipleCommandsAsync(json_data)

if __name__ == '__main__':
	debug=('--debug' in sys.argv)
	mzs=MZServer(debug)
	mzs.run()
