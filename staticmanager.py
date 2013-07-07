class StaticManager:
	def __init__(self,statics=[]):
		uid=0
		self.statics={}
		for s in statics:
			self.statics[uid]=s
			uid+=1

	def get_capabilities(self):
		l={}
		for (uid,obj) in self.statics.iteritems():
			d=obj.constants
			d.update({
			'commands':obj.commands.keys(),
			'parameters':obj.parameters.keys(),
			})
			l[uid]=d
		return l

	def get_parameter(self,static,parameter):
		return static.parameters[parameter](static)

	def get_multiple_parameters(self,static,parameter_list):
		return dict([(parameter,self.get_parameter(static,parameter)) for parameter in parameter_list])

	def bulk_get_parameters(self,parameters):
		return dict([(
			uid,
			self.get_multiple_parameters(self.statics[uid],parameter_list)
		) for (uid,parameter_list) in parameters.iteritems()])

	def tell(self,uid,cmd,args):
		if uid not in self.statics:
			raise Exception("Static identifier not found")
		static=self.statics[uid]
		if cmd not in static.commands:
			raise Exception("Command unknown to static")
		return static.commands[cmd](static,**args)

