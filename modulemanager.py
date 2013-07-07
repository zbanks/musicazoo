class ModuleManager:
	def __init__(self,modules=[]):
		self.modules=modules

	def get_capabilities(self):
		return dict([(
			module.TYPE_STRING,
			{
				'commands':module.commands.keys(),
				'parameters':module.parameters.keys(),
			}
		) for module in self.modules])

	def get_parameter(self,module,parameter):
		return module.parameters[parameter](module)

	def get_multiple_parameters(self,module,parameter_list):
		return dict([(parameter,self.get_parameter(module,parameter)) for parameter in parameter_list])

	def instantiate(self,name,*args):
		mod_class=dict([(m.TYPE_STRING,m) for m in self.modules])[name] # optimize me maybe
		return mod_class(*args)

	def tell(self,module,cmd,args):
		if cmd not in module.commands:
			raise Exception("Command unknown to module")
		return module.commands[cmd](module,*args)

