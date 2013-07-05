class VolumeModule:
	TYPE_STRING="volume"

	def __init__(self):
		self.vol=50

	def get_vol(self):
		return self.vol

	def set_vol(self,vol):
		print 'VOL CHANGE', vol
		self.vol=vol

	validCommands={
		'get_vol':get_vol,
		'set_vol':set_vol
	}
