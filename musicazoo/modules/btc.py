import Tkinter
from musicazoo.lib.graphics import FullScreenGraphics
from musicazoo.settings import COLORS
import urllib

class BTCDisplayer(FullScreenGraphics):
	def __init__(self):
		super(BTCDisplayer, self).__init__()
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,highlightthickness=0,bg=COLORS['bg'])
		self.c.pack()
		(x,y) = self.center()
		self.text=self.c.create_text((x,y), fill=COLORS['fg'], justify=Tkinter.CENTER,anchor='center', font=("Helvetica",72))

	def show(self):
		self.animate(0)
		FullScreenGraphics.show(self)

	def animate(self,state):
		self.c.itemconfig(self.text,text="mtgox: " + urllib.urlopen("http://www.biggerpackage4u.ru/api/bitcoin_price").read().strip())
		self.update()
		state=(state+1)%4
		self.defer(10000,lambda:self.animate(state))

class BTC:
	TYPE_STRING='btc'

	def __init__(self,queue,uid):
		self.queue=queue
		self.uid=uid
		self.display = BTCDisplayer()

	def play(self):
		self.display.show()

	def stop(self):
		self.display.stop()

	commands={
		'stop':stop,
	}

	parameters={
	}

