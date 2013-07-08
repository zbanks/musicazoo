import graphics
import Tkinter
import time
import vlc

class TextAndSound(graphics.FullScreenGraphics):
	def __init__(self,text):
		graphics.FullScreenGraphics.__init__(self)

		self.text=text
		self.stopped=False

		self.init()
		
		if text.hasSound:
			self.vlc_i = vlc.Instance()
			self.vlc_mp = self.vlc_i.media_player_new()
			self.vlc_media = self.vlc_i.media_new_path(text.sndfile.name)
			self.vlc_mp.set_media(self.vlc_media)

	def play(self):
		self.vlc_mp.play()
		self.vlc_mp.set_rate(float(self.text.speed))
		while self.vlc_mp.get_length()==0:
			time.sleep(0.1)
		self.text.duration+=float(self.vlc_mp.get_length())/1000/float(self.text.speed)

		self.animate()
		self.show()

		self.start=time.time()
		while not self.stopped:
			self.text.time=time.time()-self.start
			if self.text.time>=self.text.duration:
				self.stop()
			else:
				time.sleep(0.1)

	def close(self):
		self.stopped=True
		graphics.FullScreenGraphics.close(self)

	def stop(self):
		if self.text.hasSound:
			self.vlc_mp.stop()
		self.close()

	def init(self):
		pass

	def animate(self):
		pass

class Splash(TextAndSound):
	def init(self):
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,bg='black',highlightthickness=0)
		self.c.pack()
		(x,y) = self.center()
		self.textbox=self.c.create_text((x,y), text=self.text.textToShow, fill="white", justify=Tkinter.CENTER, font=("Helvetica",72), width=self.width)

