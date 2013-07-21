import Tkinter
from graphics import *

class Logo(FullScreenGraphics):
	TYPE_STRING='logo'

	def __init__(self,queue,uid):
		self.queue=queue
		self.uid=uid

		FullScreenGraphics.__init__(self)
		self.c=Tkinter.Canvas(self,width=self.width,height=self.height,bg='black',highlightthickness=0)
		self.c.pack()

		t=self.get_text()

		self.text=self.c.create_text(self.center(), fill="white", justify=Tkinter.CENTER, font=("Helvetica",72), text=t)

	def get_text(self,default='Musicazoo'):
		c=self.queue.static_capabilities()
		found_uid=None
		for (uid,static) in c.iteritems():
			if 'class' in static and static['class']=='identity' and 'name' in static['parameters']:
				found_uid=uid
				break
		if found_uid is None:
			return default
		p=self.queue.get_statics({found_uid:['name']})
		t=p[found_uid]['name']
		if t is None:
			return default
		return t

	def close(self):
		self.hide()

	commands={
	}

	parameters={
	}
