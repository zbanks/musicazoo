import Tkinter
from graphics import *

class Logo(FullScreenGraphics):
	TYPE_STRING='logo'

	def __init__(self,queue,uid):
		FullScreenGraphics.__init__(self)
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,bg='black',highlightthickness=0)
		self.c.pack()
		self.text=self.c.create_text(self.center(), fill="white", justify=Tkinter.CENTER, font=("Helvetica",72), text='Musicazoo')

	def close(self):
		self.hide()

	commands={
	}

	parameters={
	}
