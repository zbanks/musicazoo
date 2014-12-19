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
        self.playing=False
        self.playing_afters=[]
        self.last_play_time=0

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
        self.play()

    def hide(self):
        self.withdraw()
        self.update()
        self.pause()

    def pause(self):
        if not self.playing:
            return
        self.playing=False
        self.last_play_time += time.time() - self.last_show_time
        self.destroy_playing_afters()

    def play(self):
        if self.playing:
            return
        self.playing=True
        self.last_show_time=time.time()
        self.reincarnate_playing_afters()

    def sync(self,cmd):
        self.after(0,cmd)

    def destroy_playing_afters(self):
        for (msecs,func,handle) in self.playing_afters:
            self.after_cancel(handle)

    def reincarnate_playing_afters(self):
        t=int(self.last_play_time*1000)
        self.playing_afters = [(msecs,func,self.after(max(msecs-t,0),func)) for (msecs,func,handle) in self.playing_afters if msecs-t > 0]

    def play_time(self):
        if self.playing:
            return self.last_play_time+time.time()-self.last_show_time
        return self.last_play_time

    def after_playing(self,msecs,func):
        if self.playing:
            handle=self.after(msecs,func)
            self.playing_afters.append((msecs+int(self.play_time()*1000),func,handle))
        else:
            self.playing_afters.append((msecs+int(self.last_play_time*1000),func,None))

if __name__=='__main__':
    fsg=FullScreenGraphics()

    c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,highlightthickness=0,bg="black")
    c.pack()

    coord = fsg.center()
    arc = c.create_text(coord, text="Loading", fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))

    fsg.after(100, fsg.show)
    fsg.after(3000, fsg.over)
    fsg.run()
