import Tkinter
import threading
import time

COLORS = {
    "bg" : "#406873",
    "fg" : "#F3FDE1"
}

class FullScreenGraphics(Tkinter.Tk,threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon=True
		self.ready=threading.Semaphore(0)
		self.start()
		self.ready.acquire()

	def run(self):
		Tkinter.Tk.__init__(self)
		self.configure(background=COLORS['bg'])
		self.withdraw()
		self.width,self.height=self.winfo_screenwidth(),self.winfo_screenheight()
		self.attributes('-fullscreen', True)
		self.bind("<Escape>", self.over)
		self.finished=False
		self.after(0,lambda:self.ready.release())
		self.mainloop()
		self.finished=True

	def center(self):
		return (self.width/2,self.height/2)

	def over(self,event=None):
		self.destroy()

	def close(self):
		if not self.finished:
			self.after(0,self.over)
		self.join()

	def show(self):
		self.after(0,self.show_sync)

	def show_sync(self):
		self.deiconify()
		self.update()

	def hide(self):
		self.after(0,self.hide_sync)

	def hide_sync(self):
		self.withdraw()
		self.update()

if __name__=='__main__':
	fsg=FullScreenGraphics()

	c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,highlightthickness=0,**COLORS)
	c.pack()

	coord = fsg.center()
	arc = c.create_text(coord, text="Loading", fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))

	fsg.show()
	time.sleep(3)
	fsg.close()
