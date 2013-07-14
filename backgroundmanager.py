class BackgroundManager:
	def __init__(self,backgrounds=[]):
		self.backgrounds=backgrounds

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
			background.TYPE_STRING,
			{
				'commands':background.commands.keys(),
				'parameters':background.parameters.keys(),
			}
		) for background in self.backgrounds])
		return {'commands':self.universal_commands.keys(),'parameters':self.universal_parameters.keys(),'specifics':cap}

	def get_parameter(self,background,parameter):
		if parameter in self.universal_parameters:
			return self.universal_parameters[parameter](background)
		if parameter in background.parameters:
			return background.parameters[parameter](background)
		raise Exception("Background has no such parameter")

	def get_multiple_parameters(self,background,parameter_list):
		return dict([(parameter,self.get_parameter(background,parameter)) for parameter in parameter_list])

	def instantiate(self,name,args):
		bg_class=dict([(bg.TYPE_STRING,bg) for bg in self.backgrounds])[name] # optimize me maybe
		return bg_class(**args)

	def tell(self,background,cmd,args):
		if cmd in self.universal_commands:
			return self.universal_commands[cmd](background,**args)
		if cmd in background.commands:
			return background.commands[cmd](background,**args)
		raise Exception("Background has no such command")

