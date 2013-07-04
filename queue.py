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

	def doCommand(self,line):
		try:
			cmd=line['cmd'] # Fails if no cmd given
		except KeyError:
			return self.errorPacket('No command given.')

		try:
			targ=line['target'] # Target is self if not given
			try:
				obj=dict(self.queue+self.statics)[targ] # Fails if target does not exist
			except KeyError:
				return self.errorPacket('Bad target.')
		except KeyError:
			obj=self

		try:
			args=line['args']
		except KeyError:
			args=[]

		try:
			args=list(args)
		except TypeError:
			return self.errorPacket('Argument list not a list.')

		try:
			f=obj.validCommands[cmd]
		except KeyError:	
			return self.errorPacket('Bad command.')

		result=f(obj,*args)

		return self.goodPacket(result)

	def errorPacket(self,err):
		return {'success':False,'error':err}

	def goodPacket(self,payload):
		return {'success':True,'result':payload}

	validCommands={
		'help':getHelp
	}

# End class MZQueue

