from musicazoo.lib.graphics import FullScreenGraphics
import Tkinter
import datetime

class Clock(FullScreenGraphics):
	TYPE_STRING='clock'

	def __init__(self,queue,uid):
		FullScreenGraphics.__init__(self)

		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,bg='black',highlightthickness=0)
		self.c.pack()

		self.text=self.c.create_text(self.center(), fill='white', justify=Tkinter.CENTER, font=("Helvetica",72))
		self.animate()

	def get_time(self):
		return datetime.datetime.now().strftime('%H:%M:%S')

	def animate(self):
		self.c.itemconfig(self.text,text=self.get_time())
		self.update()
		self.defer(1000,self.animate)

	parameters={
		'time':get_time
	}

	commands={
	}
