import Tkinter
import time

from musicazoo.settings import COLORS
from musicazoo.lib import vlc
from musicazoo.lib.graphics import FullScreenGraphics

PADY=10
PADX=10


class TextAndSound(FullScreenGraphics):
	def __init__(self,text):
		super(TextAndSound, self).__init__()

		self.text=text
		self.stopped=False
		self.audio_duration=None

		self.init()
		
		if text.hasSound:
			self.vlc_i = vlc.Instance()
			self.vlc_mp = self.vlc_i.media_player_new()
			self.vlc_media = self.vlc_i.media_new_path(text.sndfile.name)
			self.vlc_mp.set_media(self.vlc_media)

	def play(self):
		self.vlc_mp.play()
		self.vlc_mp.set_rate(float(self.text.speed))
		while True:
			d=self.vlc_mp.get_length()
			if d>0:
				break
			time.sleep(0.1)
		self.audio_duration=float(d)/1000/float(self.text.speed)
		self.text.duration+=self.audio_duration

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
		super(TextAndSound, self).close()

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
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,bg=COLORS['bg'],highlightthickness=0)
		self.c.pack()
		(x,y) = self.center()
		self.textbox=self.c.create_text((x,y), text=self.text.textToShow, fill=COLORS['fg'], justify=Tkinter.CENTER, font=("Arial",72), width=self.width)

class MonoParagraph(TextAndSound):
	def init(self):
		self.textbox = Tkinter.Text(self,
			font=("Mono", 32),
			wrap=Tkinter.WORD,
			highlightthickness=0,
			relief=Tkinter.FLAT,
			**COLORS)
		self.textbox.insert(Tkinter.END, self.text.textToShow)
		self.textbox.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, padx=PADX)

class Email(TextAndSound):
	def init(self):
		sender = self.text.textToShow['sender']
		subject = self.text.textToShow['subject']
		body = self.text.textToShow['body']

		self.beginning_dead_time=18
		self.end_dead_time=-3

		self.configure(background=COLORS['bg'])

		self.wf = Tkinter.Label(self, 
			font=("Arial", 36), 
			wraplength=self.width,
			text=sender,
			**COLORS)
		self.wf.pack(padx=PADX)
		self.wt = Tkinter.Label(self, 
			font=("Arial", 48), 
			wraplength=self.width,
			text=subject,
			**COLORS)
		self.wt.pack(padx=PADX)

		self.w = Tkinter.Text(self,
			font=("Arial", 36),
			wrap=Tkinter.WORD,
			highlightthickness=0,
			relief=Tkinter.FLAT,
			**COLORS)

		self.w.insert(Tkinter.END, body)
		self.w.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, padx=PADX)

	def animate(self):
		self.time_started=time.time()
		self.scroll()

	def scroll(self):
		t=time.time()-self.time_started
		if t<self.beginning_dead_time:
			fraction=0
		elif t<self.audio_duration-self.end_dead_time:
			fraction=(t-self.beginning_dead_time)/(self.audio_duration-self.end_dead_time-self.beginning_dead_time)
		else:
			fraction=1

		self.w.yview_moveto(fraction)

		self.defer(10,self.scroll)
