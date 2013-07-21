class Identity:

	def __init__(self,name=None,location=None):
		self.name=name
		self.location=location

	def get_name(self):
		return self.name

	def get_location(self):
		return self.location

	commands={
	}

	parameters={
		'name':get_name,
		'location':get_location,
	}

	constants={
		'class':'identity'
	}
