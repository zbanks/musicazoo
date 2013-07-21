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
        text = self.text.textToShow
        send_line, _, text = text.partition('\n')
        subject_line, _, text = text.partition('\n')

        s_width = self.winfo_screenwidth() - 1
        s_height = self.winfo_screenheight() - 1
        self.geometry("{0}x{1}+0+0".format(s_width, s_height))

        self.wf = Tkinter.Label(self, 
                                font=("Arial", 48), 
                                bg=COLORS['bg'], 
                                fg=COLORS['fg'], 
                                wraplength=s_width,
                                text=send_line)
        self.wf.pack(padx=PADX)
        self.wt = Tkinter.Label(self, 
                                font=("Arial", 48), 
                                bg=COLORS['bg'], 
                                fg=COLORS['fg'], 
                                wraplength=s_width,
                                text=subject_line)
        self.wt.pack(padx=PADX)

        self.w = Tkinter.Text(self,
                              font=("Arial", 36),
                              wrap=Tkinter.WORD,
                              highlightthickness=0,
                              relief=Tkinter.FLAT,
                              **COLORS)
        self.w.insert(Tkinter.END, text)
        self.w.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, padx=PADX)
