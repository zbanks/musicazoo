import Tkinter
from graphics import *

class LoadingScreen(FullScreenGraphics):
	def __init__(self):
		FullScreenGraphics.__init__(self)
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,bg='black',highlightthickness=0)
		self.c.pack()
		coord = self.center()
		text = self.c.create_text(coord, text="Loading", fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))
