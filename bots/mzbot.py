# A simple bot framework

import httplib
import json

class MZBot:
	def __init__(self,server,port):
		self.server=server
		self.port=port

	def doCommands(self,cmdlist):
		cmdlist_json=json.dumps(cmdlist)
		h=httplib.HTTPConnection(self.server,self.port)
		headers = {"Content-type": "text/json"}
		h.request("POST", "", cmdlist_json, headers)
		response_json=h.getresponse().read()
		response=json.loads(response_json)
		return response

if __name__=='__main__':
	b=MZBot('localhost','9000')
	print b.doCommands([{'cmd':'static_capabilities'}])
