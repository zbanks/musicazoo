import Tkinter
import cStringIO
import urllib
from graphics import *
from PIL import Image, ImageTk

class ImageBG(FullScreenGraphics):
	TYPE_STRING='image'

	def __init__(self,queue,uid,image):
		FullScreenGraphics.__init__(self)
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,bg='black',highlightthickness=0)
		self.c.pack()
		self.url=image
		self.queue=queue
		self.uid=uid
		self.tkimg=self.c.create_image(*self.center())
		self.status='loading'

		t=threading.Thread(target=self.load)
		t.daemon=True
		t.start()

	def load(self):
		try:
			#print "Reading URL..."
			f = cStringIO.StringIO(urllib.urlopen(self.url).read())
			#print "Opening Image..."
			i=Image.open(f)
			#print "Scaling Image..."
			i.thumbnail((self.width,self.height),Image.ANTIALIAS)
			self.image=ImageTk.PhotoImage(i)
			self.updateImage()
			#print "Done."
			self.status='ready'
		except Exception:
			self.status='failed'
			self.queue.removeMeAsync(self.uid)
			raise
		
	def updateImage(self):
		self.after(0,lambda:self.c.itemconfig(self.tkimg,image=self.image))

	def get_status(self):
		return self.status

	def get_url(self):
		return self.url

	commands={
	}

	parameters={
		'status':get_status,
		'url':get_url,
	}
