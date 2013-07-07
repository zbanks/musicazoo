import Tkinter
import threading
import time

class FullScreenGraphics(Tkinter.Tk):
	def __init__(self):
		Tkinter.Tk.__init__(self)
		self.withdraw()
		self.width,self.height=self.winfo_screenwidth(),self.winfo_screenheight()
		self.attributes('-fullscreen', True)
		self.bind("<Escape>", self.close)

	def center(self):
		return (self.width/2,self.height/2)

	def close(self,event=None):
		self.destroy()

	def show(self):
		self.deiconify()
		self.update()

	def hide(self):
		self.withdraw()
		self.update()

if __name__=='__main__':
	fsg=FullScreenGraphics()

	c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,bg='black',highlightthickness=0)
	c.pack()

	coord = fsg.center()
	arc = c.create_text(coord, text="Loading", fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))

	fsg.show()
	time.sleep(5)
	fsg.close()
	#fsg.top.mainloop()
