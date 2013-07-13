import mplayer
import os
import time

class Player:
	def __init__(self):
		self.loaded=False
		self.l=None
		self.sl=None
		self.t=None

	def load(self,media,cookies=None):
		os.environ["DISPLAY"] = ":0"
		args=['-fs','-http-header-fields','User-Agent: Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11']
		if cookies is not None:
			args+=['-cookies','-cookies-file',cookies,media]
		self.mp=mplayer.Player(args=args)
		self.loaded=True

	def up(self):
		if not self.loaded:
			return False

		if self.length() is None:
			return True # Wait for video to show up

		return self.mp.width is not None

	def play(self):
		if self.mp.paused:
			self.mp.pause()

	def pause(self):
		if not self.mp.paused:
			self.mp.pause()

	def stop(self):
		self.mp.quit()

	def set_rate(self,rate):
		self.mp.speed=rate

	def get_rate(self):
		return self.mp.speed

	def length(self):
		if self.l is None:
			self.l=self.mp.length
		return self.l

	def stream_length(self):
		if self.sl is None:
			self.sl=self.mp.stream_length
		return self.sl

	def time(self):
		sp=self.mp.stream_pos
		l=self.length()
		sl=self.stream_length()
		if sp is not None and l is not None and sl is not None:
			self.t=l*sp/sl
		return self.t

