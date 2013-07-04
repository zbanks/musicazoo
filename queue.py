# All things that take commands need a validCommands dict pointing to their functions.

# Command format:
# { target: num,
#   cmd: 'cmd',
#   args: [] }
#
# no target: operate on queue
# no args: ok

import yt

class MZQueue:
	def __init__(self,statics=[]):
		self.queue=[]
		self.statics=[]
		self.uid=1
		for s in statics:
			self.statics.append((self.uid,s))
			self.updateUID()

	def updateUID(self):
		self.uid+=1

	def getHelp(self):
		return str(validCommands.keys())

	def lsQueue(self):
		return [{'uid':i,'type':obj.TYPE_STRING} for (i,obj) in self.queue]

	def lsStatics(self):
		return [{'uid':i,'type':obj.TYPE_STRING} for (i,obj) in self.statics]

	def addModule(self,name,*args):
		mod_type=dict([(m.TYPE_STRING,m) for m in self.validModules])[name] # optimize me maybe
		mod_inst=mod_type(*args)
		self.queue.append((self.uid,mod_inst))
		self.updateUID()

	def doCommand(self,line):
		if not isinstance(line,dict):
			return errorPacket('Command not a dict.')

		try:
			cmd=line['cmd'] # Fails if no cmd given
		except KeyError:
			return errorPacket('No command given.')

		try:
			targ=line['target'] # Target is self if not given
			try:
				obj=dict(self.queue+self.statics)[targ] # Fails if target does not exist
			except KeyError:
				return errorPacket('Bad target.')
		except KeyError:
			obj=self

		try:
			args=line['args']
		except KeyError:
			args=[]

		if not isinstance(args,list):
			return errorPacket('Argument list not a list.')

		try:
			f=obj.validCommands[cmd]
		except KeyError:	
			return errorPacket('Bad command.')

		try:
			result=f(obj,*args)
		except Exception as e:
			return errorPacket(str(e))

		return goodPacket(result)

	validCommands={
		'help':getHelp,
		'queue':lsQueue,
		'statics':lsStatics,
		'add':addModule
	}

	validModules=[
		yt.YoutubeModule
	]

# End class MZQueue
def errorPacket(err):
	return {'success':False,'error':err}

def goodPacket(payload):
	if payload is not None:
		return {'success':True,'result':payload}
	return {'success':True}

if __name__=='__main__':
	q=MZQueue()
	print q.addModule('youtube','google.com')
	print q.lsQueue()
