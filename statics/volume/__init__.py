import alsaaudio

class Volume:
	def __init__(self):
		self.mixer=alsaaudio.Mixer()

	def get_vol(self):
		return int(self.mixer.getvolume()[0])

	def set_vol(self,vol):
		self.mixer.setvolume(vol)

	commands={
		'set_vol':set_vol
	}

	parameters={
		'vol':get_vol
	}

	constants={
		'class':'volume'
	}
