import Tkinter
from graphics import *

class LoadingScreen(FullScreenGraphics):
	def __init__(self):
		FullScreenGraphics.__init__(self)
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,bg='black',highlightthickness=0)
		self.c.pack()
		(x,y) = self.center()
		self.text=self.c.create_text((x-250,y), fill="white", justify=Tkinter.CENTER,anchor='w', font=("Helvetica",72))

	def show(self):
		self.animate(0)
		FullScreenGraphics.show(self)

	def animate(self,state):
		self.c.itemconfig(self.text,text="Loading"+'.'*state)
		self.update()
		state+=1
		if state>3:
			state=0
		self.after(300,lambda:self.animate(state))
