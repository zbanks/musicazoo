import Tkinter
from musicazoo.lib.graphics import FullScreenGraphics
from musicazoo.settings import COLORS

class LoadingScreen(FullScreenGraphics):
	def __init__(self):
		super(LoadingScreen, self).__init__()
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,highlightthickness=0,bg=COLORS['bg'])
		self.c.pack()
		(x,y) = self.center()
		self.text=self.c.create_text((x-250,y), fill=COLORS['fg'], justify=Tkinter.CENTER,anchor='w', font=("Helvetica",72))
		self.animate(0)

	def animate(self,state):
		self.c.itemconfig(self.text,text="Loading"+'.'*state)
		self.update()
		state=(state+1)%4
		self.defer(300,lambda:self.animate(state))
