import Tkinter
import time
import os

class FullScreenGraphics(Tkinter.Tk):
    def __init__(self):
        Tkinter.Tk.__init__(self)
        self.withdraw()
        self.width,self.height=self.winfo_screenwidth(),self.winfo_screenheight()
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", self.over)

    def run(self):
        self.mainloop()

    def center(self):
        return (self.width/2,self.height/2)

    def over(self,event=None):
        self.destroy()

    def show(self):
        try:
            os.system("xset dpms force on")
        except Exception:
            pass
        self.deiconify()
        self.update()

    def hide(self):
        self.withdraw()
        self.update()

    def sync(self,cmd):
        self.after(0,cmd)

if __name__=='__main__':
    fsg=FullScreenGraphics()

    c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,highlightthickness=0,bg="black")
    c.pack()

    coord = fsg.center()
    arc = c.create_text(coord, text="Loading", fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))

    fsg.after(100, fsg.show)
    fsg.after(3000, fsg.over)
    fsg.run()
