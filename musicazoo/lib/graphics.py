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
        self.shown=False
        self.visible_afters=[]
        self.last_visible_time=0

    def run(self):
        self.mainloop()

    def center(self):
        return (self.width/2,self.height/2)

    def over(self,event=None):
        self.destroy()

    def show(self):
        if self.shown:
            return
        try:
            os.system("xset dpms force on")
        except Exception:
            pass
        self.deiconify()
        self.update()
        self.shown=True
        self.last_show_time=time.time()
        self.destroy_visible_afters()

    def hide(self):
        if not self.shown:
            return
        self.withdraw()
        self.update()
        self.shown=False
        self.last_visible_time += time.time() - self.last_show_time
        self.reincarnate_visible_afters()

    def sync(self,cmd):
        self.after(0,cmd)

    def destroy_visible_afters(self):
        for (msecs,func,handle) in self.visible_afters:
            self.cancel_after(handle)

    def reincarnate_visible_afters(self):
        t=int(self.last_visible_time*1000)
        self.visible_afters = [(msecs,func,self.after(max(msecs-t,0),func)) for (msecs,func,handle) in self.visible_afters if msecs-t > 0]

    def visible_time(self):
        if self.shown:
            return self.last_visible_time+time.time()-self.last_show_time
        return self.last_visible_time

    def after_visible(self,msecs,func):
        if self.shown:
            handle=self.after(msecs,func)
            self.visible_afters.append((msecs+int(self.visible_time()*1000),func,handle))
        else:
            self.visible_afters.append((msecs+int(self.last_visible_time*1000),func,None))

if __name__=='__main__':
    fsg=FullScreenGraphics()

    c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,highlightthickness=0,bg="black")
    c.pack()

    coord = fsg.center()
    arc = c.create_text(coord, text="Loading", fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))

    fsg.after(100, fsg.show)
    fsg.after(3000, fsg.over)
    fsg.run()
