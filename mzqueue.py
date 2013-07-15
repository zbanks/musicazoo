import threading
import time

class MZQueue:
	def __init__(self,module_manager,static_manager,background_manager):
		self.queue=[]
		self.cur=None
		self.bg=None
		self.modules=module_manager
		self.statics=static_manager
		self.backgrounds=background_manager
		self.lock=threading.Semaphore()		# Used to avoid queue concurrency issues
		self.wakeup=threading.Semaphore()	# Used to wake up the thread manager when something is added to the queue 

	# queue command
	def get_queue(self,parameters={}):
		l=[]
		for (uid,obj) in self.queue:
			d={'uid':uid,'type':obj.TYPE_STRING}
			if obj.TYPE_STRING in parameters:
				d['parameters']=self.modules.get_multiple_parameters(obj,parameters[obj.TYPE_STRING])
			l.append(d)
		return l

	# cur command
	def get_cur(self,parameters={}):
		if self.cur is None:
			return None

		(uid,obj)=self.cur

		d={'uid':uid,'type':obj.TYPE_STRING}
		if obj.TYPE_STRING in parameters:
			d['parameters']=self.modules.get_multiple_parameters(obj,parameters[obj.TYPE_STRING])

		return d

	def get_bg(self,parameters={}):
		if self.bg is None:
			return None

		(uid,obj)=self.bg

		d={'uid':uid,'type':obj.TYPE_STRING}
		if obj.TYPE_STRING in parameters:
			d['parameters']=self.backgrounds.get_multiple_parameters(obj,parameters[obj.TYPE_STRING])
		return d

	def set_bg(self,type,args={}):
		uid=self.backgrounds.get_uid()
		mod_inst=self.backgrounds.instantiate(type,self,uid,args)
		if self.bg is not None:
			(bg_uid,bg_obj)=self.bg
			bg_obj.close()
		self.bg=(uid,mod_inst)
		self.bg_visible=False
		self.update_bg()
		return {'uid':uid}

	def update_bg(self,parameters={}):
		if self.bg is None:
			return
		
		(bg_uid,bg_obj)=self.bg
		if self.cur is None:
			if not self.bg_visible:
				bg_obj.show()
				self.bg_visible=True
		else:
			if self.bg_visible:
				bg_obj.hide()
				self.bg_visible=False

	# add command
	def add(self,type,args={}):
		uid=self.modules.get_uid()
		mod_inst=self.modules.instantiate(type,self,uid,args)
		self.queue.append((uid,mod_inst))
		self.wakeup.release()
		return {'uid':uid}

	def rm(self,uids):
		self.queue=[(uid,obj) for (uid,obj) in self.queue if uid not in [int(uid) for uid in uids]]

	def mv(self,uids):
		newqueue=[]
		oldqueue=[uid for (uid,obj) in self.queue]
		d=dict(self.queue)
		for uid in uids:
			uid=int(uid)
			if uid in oldqueue:
				oldqueue.remove(uid)
				newqueue.append(uid)
		newqueue+=oldqueue
		self.queue=[(uid,d[uid]) for uid in newqueue]

	def get_statics(self,parameters):
		return self.statics.bulk_get_parameters(parameters)

	def static_capabilities(self):
		return self.statics.get_capabilities()

	def module_capabilities(self):
		return self.modules.get_capabilities()

	def background_capabilities(self):
		return self.backgrounds.get_capabilities()

	def tell_module(self,uid,cmd,args={}):
		uid=int(uid)
		d=self.available_modules()
		if uid not in d:
			raise Exception("Module identifier not in queue or cur")
		return self.modules.tell(d[uid],cmd,args)

	def tell_background(self,uid,cmd,args={}):
		uid=int(uid)
		if self.bg is None:
			raise Exception("No background")
		(bg_uid,bg_obj)=self.bg
		if bg_uid != uid:
			raise Exception("Bad background")
		return self.backgrounds.tell(bg_obj,cmd,args)

	def available_modules(self):
		if self.cur is None:
			return dict(self.queue)
		return dict(self.queue+[self.cur])

	def ask_module(self,uid,parameters):
		uid=int(uid)
		d=self.available_modules()
		if uid not in d:
			raise Exception("Module identifier not in queue or cur")
		return self.modules.get_multiple_parameters(d[uid],parameters)

	def ask_background(self,uid,parameters):
		uid=int(uid)
		if self.bg is None:
			raise Exception("No background")
		(bg_uid,bg_obj)=self.bg
		if bg_uid != uid:
			raise Exception("Bad background")
		return self.modules.get_multiple_parameters(bg_obj,parameters)

	def tell_static(self,uid,cmd,args={}):
		uid=int(uid)
		return self.statics.tell(uid,cmd,args)

	# Changes out the current module for the top of the queue
	def next(self):
		if len(self.queue)==0:
			self.cur=None
		else:
			self.cur=self.queue.pop(0)
		self.update_bg()
		return self.cur is not None

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

	# Removes a module asynchronously
	def removeMeAsync(self,uid):
		self.sync(lambda:self.rm([uid]))

	# Parse and run a command
	def doCommand(self,line):
		if not isinstance(line,dict):
			return errorPacket('Command not a dict.')

		try:
			cmd=line['cmd'] # Fails if no cmd given
		except KeyError:
			return errorPacket('No command given.')

		try:
			args=line['args']
		except KeyError:
			args={}

		if not isinstance(args,dict):
			return errorPacket('Argument list not a dict.')

		try:
			f=self.commands[cmd]
		except KeyError:	
			return errorPacket('Bad command.')

		try:
			result=f(self,**args)
		except Exception as e:
			raise
			return errorPacket(str(e))

		return goodPacket(result)

	commands={
		'rm':rm,
		'mv':mv,
		'add':add,
		'queue':get_queue,
		'cur':get_cur,
		'statics':get_statics,
		'bg':get_bg,
		'set_bg':set_bg,
		'static_capabilities':static_capabilities,
		'module_capabilities':module_capabilities,
		'background_capabilities':background_capabilities,
		'tell_module':tell_module,
		'tell_static':tell_static,
		'tell_background':tell_background,
		'ask_module':ask_module,
		'ask_background':ask_background,
	}

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
			if self.mzq.nextAsync(): # Switch out module
				self.mzq.cur[1].play() # Block here while playing
			else:
				self.mzq.wakeup.acquire() # Block here if no more things to play

# End class MZQueueManager

# Useful JSONification functions

def errorPacket(err):
	return {'success':False,'error':err}

def goodPacket(payload):
	if payload is not None:
		return {'success':True,'result':payload}
	return {'success':True}

