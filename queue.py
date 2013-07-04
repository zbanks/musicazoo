# All things that take commands need a validCommands dict pointing to their functions.

# Command format:
# { target: num,
#   cmd: 'cmd',
#   args: [] }
#
# no target: operate on queue
# no args: ok

class MZQueue:
	def __init__(self,statics=[]):
		self.queue=[]
		self.statics=[]

	def getHelp(self):
		return "Try harder."

	def lsQueue(self):
		return [i,obj.TYPESTR for (i,obj) in self.queue]

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

		result=f(obj,*args)

		return goodPacket(result)

	validCommands={
		'help':getHelp,
		'ls':lsQueue
	}

	validModules={
		'youtube

# End class MZQueue
def errorPacket(err):
	return {'success':False,'error':err}

def goodPacket(payload):
	return {'success':True,'result':payload}

