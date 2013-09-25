import Tkinter
import threading
import time
import os

class FullScreenGraphics(Tkinter.Tk,threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon=True
		self.ready=threading.Semaphore(0)
		self.defer_lock=threading.Semaphore()
		self.deferred_commands=set()
		self.start()
		self.ready.acquire()

	def defer(self,wait,command):
		def _deferred():
			self.defer_lock.acquire()
			self.deferred_commands.remove(handle)
			self.defer_lock.release()
			command()

		self.defer_lock.acquire()
		handle=self.after(wait, _deferred)
		self.deferred_commands.add(handle)
		self.defer_lock.release()

	def run(self):
		Tkinter.Tk.__init__(self)
		self.withdraw()
		self.width,self.height=self.winfo_screenwidth(),self.winfo_screenheight()
		self.attributes('-fullscreen', True)
		self.bind("<Escape>", self.over)
		self.finished=False
		self.defer(0,lambda:self.ready.release())
		self.mainloop()
		self.finished=True

	def center(self):
		return (self.width/2,self.height/2)

	def over(self,event=None):
		self.defer_lock.acquire()
		for after_handle in self.deferred_commands:
			self.after_cancel(after_handle)
		self.destroy()

	def close(self):
		if not self.finished:
			self.defer(0,self.over)
		self.join()

	def show_sync(self):
		try:
			os.system("xset dpms force on")
		except Exception:
			pass
		self.deiconify()
		self.update()

	def show(self):
		if not self.finished:
			self.defer(0,self.show_sync)

	def hide_sync(self):
		self.withdraw()
		self.update()

	def hide(self):
		if not self.finished:
			self.defer(0,self.hide_sync)

if __name__=='__main__':
	fsg=FullScreenGraphics()

	c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,highlightthickness=0)
	c.pack()

	coord = fsg.center()
	arc = c.create_text(coord, text="Loading", fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))

	fsg.show()
	time.sleep(3)
	fsg.close()
