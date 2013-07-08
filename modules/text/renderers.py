import graphics
import Tkinter
import time

def splash(obj):
	fsg=graphics.FullScreenGraphics()
	c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,bg='black',highlightthickness=0)
	c.pack()
	(x,y) = fsg.center()
	text=c.create_text((x,y), text=obj.textToShow, fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))
	fsg.show()
	time.sleep(obj.duration)
	fsg.close()
