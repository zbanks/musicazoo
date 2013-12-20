import Tkinter
from musicazoo.lib.graphics import FullScreenGraphics
from musicazoo.settings import COLORS
import urllib
import threading

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
		self.lock = threading.Lock()
		self.lock.acquire()

	def play(self):
		self.display.show()
		self.lock.acquire()

	def stop(self):
		self.display.close()
		self.lock.release()

	commands={
		'stop':stop,
	}

	parameters={
		'status':lambda x:'playing',
	}

