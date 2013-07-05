# All things that take commands need a validCommands dict pointing to their functions.

# Command format:
# { target: num,
#   cmd: 'cmd',
#   args: [] }
#
# no target: operate on queue
# no args: ok

import threading
import time
import yt

class MZQueue:
	def __init__(self,statics=[]):
		self.queue=[]
		self.cur=None
		self.statics=[]
		self.uid=1
		self.lock=threading.Semaphore()		# Used to avoid queue concurrency issues
		self.wakeup=threading.Semaphore()	# Used to wake up the thread manager when something is added to the queue 

		# Loop through all the statics we want to add, and assign the UIDs
		for s in statics:
			self.statics.append((self.uid,s))
			self.updateUID()

	def updateUID(self):
		self.uid+=1

	# help command
	def getHelp(self):
		return str(validCommands.keys())

	# queue command
	def lsQueue(self):
		return [{'uid':i,'type':obj.TYPE_STRING} for (i,obj) in self.queue]

	# cur command
	def lsCur(self):
		return [{'uid':self.cur[0],'type':self.cur[1].TYPE_STRING}] if self.cur else []

	# statics command
	def lsStatics(self):
		return [{'uid':i,'type':obj.TYPE_STRING} for (i,obj) in self.statics]

	# add command
	def addModule(self,name,*args):
		mod_type=dict([(m.TYPE_STRING,m) for m in self.validModules])[name] # optimize me maybe
		mod_inst=mod_type(*args)
		self.queue.append((self.uid,mod_inst))
		self.wakeup.release()
		self.updateUID()

	# Changes out the current module for the top of the queue
	def next(self):
		if len(self.queue)==0:
			self.cur=None
			return False
		self.cur=self.queue.pop(0)
		return True

	# Runs a set of commands. Queue is guarenteed to not change during them.
	def doMultipleCommandsAsync(self,commands):
		return self.sync(lambda:[self.doCommand(cmd) for cmd in commands])

	# Calls next() function once lock is acquired
	def nextAsync(self):
		return self.sync(self.next)

	# Acquires this object's lock and executes the given cmd
	def sync(self,cmd):
		try:
			self.lock.acquire()
			result=cmd()
		except Exception:
			self.lock.release()
			raise
		self.lock.release()
		return result

	# Parse and run a command
	def doCommand(self,line):
		if not isinstance(line,dict):
			return errorPacket('Command not a dict.')

		try:
			cmd=line['cmd'] # Fails if no cmd given
		except KeyError:
			return errorPacket('No command given.')

		try:
			targ=line['target'] # Target is self if not given
			print self.queue
			print self.statics
			print self.cur
			lookup_dict = dict(self.queue + self.statics + ([self.cur] or []))
			if targ in lookup_dict:
				obj = lookup_dict[targ] # Fails if target does not exist
			else:
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
		'add':addModule,
		'cur':lsCur
	}

	validModules=[
		yt.YoutubeModule
	]

# End class MZQueue

# This class actually plays modules and switches them out as they finish
# It runs in its own thread so the play() method in modules should block.

class MZQueueManager(threading.Thread):
	def __init__(self,mzq):
		self.mzq=mzq
		super(MZQueueManager,self).__init__()

	def start(self):
		self.daemon=True
		super(MZQueueManager,self).start()

	def run(self):
		while True:
			self.mzq.wakeup.acquire() # Block here if no more things to play
			if self.mzq.nextAsync(): # Switch out module
				self.mzq.cur[1].play() # Block here while playing

# End class MZQueueManager

# Useful JSONification functions

def errorPacket(err):
	return {'success':False,'error':err}

def goodPacket(payload):
	if payload is not None:
		return {'success':True,'result':payload}
	return {'success':True}

