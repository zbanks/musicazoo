import vlc
import os

class Player:
	def __init__(self):
		self.loaded=False

	def load(self,media,cookies=None):
		os.environ["DISPLAY"] = ":0"
		self.vlc_i = vlc.Instance(['-f','--no-video-title-show'])
		self.vlc_mp = self.vlc_i.media_player_new()
		vlc_media=self.vlc_i.media_new_location(media)
		self.vlc_mp.set_media(vlc_media)
		self.vlc_mp.set_xwindow(0)
		self.vlc_mp.set_fullscreen(True)
		self.vlc_mp.play()
		self.loaded=True

	def up(self):
		if not self.loaded:
			return False

		# Perhaps change this to be in the positive
		return self.vlc_mp.get_state() not in [vlc.State.Ended,vlc.State.Stopped,vlc.State.Error]

	def play(self):
		self.vlc_mp.play()

	def pause(self):
		self.vlc_mp.pause()

	def stop(self):
		self.vlc_mp.stop()

	def set_rate(self,rate):
		self.vlc_mp.set_rate(rate)

	def get_rate(self):
		return self.vlc_mp.get_rate()

	def length(self):
		l=self.vlc_mp.get_length()
		if l<=0:
			return None
		return float(l)/1000

	def time(self):	
		t=self.vlc_mp.get_time()
		return float(t)/1000
