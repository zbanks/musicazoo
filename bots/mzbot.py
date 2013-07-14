# A simple bot framework

import httplib
import json

class MZBot:
	def __init__(self,server='localhost',port=9000,path=''):
		self.server=server
		self.port=port
		self.path=path

	def doCommands(self,cmdlist):
		cmdlist_json=json.dumps(cmdlist)
		h=httplib.HTTPConnection(self.server,self.port)
		headers = {"Content-type": "text/json"}
		h.request("POST", '/'+self.path, cmdlist_json, headers)
		response_json=h.getresponse().read()
		response=json.loads(response_json)
		return response

	def assert_success(self,result):
		if isinstance(result,dict):
			if result['success']:
				return
			raise Exception(result['error'])
		
		if isinstance(result,list):
			for r in result:
				if not r['success']:
					raise Exception(r['error'])
				return
		raise Exception('Bad response type from server')

if __name__=='__main__':
	b=MZBot('localhost','9000')
	print b.doCommands([{'cmd':'static_capabilities'}])
