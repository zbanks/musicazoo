class ModuleManager(object):
	def __init__(self,modules=[]):
		self.modules=modules

		self.universal_commands={
		}

		self.universal_parameters={
			'str':str
		}

		self.uid=0

	def get_uid(self):
		uid=self.uid
		self.uid+=1
		return uid

	def get_capabilities(self):
		cap=dict([(
			module.TYPE_STRING,
			{
				'commands':module.commands.keys(),
				'parameters':module.parameters.keys(),
			}
		) for module in self.modules])
		return {'commands':self.universal_commands.keys(),'parameters':self.universal_parameters.keys(),'specifics':cap}

	def get_parameter(self,module,parameter):
		if parameter in self.universal_parameters:
			return self.universal_parameters[parameter](module)
		if parameter in module.parameters:
			return module.parameters[parameter](module)
		raise Exception("Module has no such parameter")

	def get_multiple_parameters(self,module,parameter_list):
		return dict([(parameter,self.get_parameter(module,parameter)) for parameter in parameter_list])

	def instantiate(self,name,queue,uid,args):
		if 'queue' in args or 'uid' in args:
			raise Exception('arg list cannot contain queue or uid')
		mod_class=dict([(m.TYPE_STRING,m) for m in self.modules])[name] # optimize me maybe
		return mod_class(queue,uid,**args)

	def tell(self,module,cmd,args):
		if cmd in self.universal_commands:
			return self.universal_commands[cmd](module,**args)
		if cmd in module.commands:
			return module.commands[cmd](module,**args)
		raise Exception("Module has no such command")

