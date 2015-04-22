from shmooze.modules import JSONParentPoller
import musicazoo.lib.graphics
import shmooze.settings as sets
import threading
import socket
import Tkinter
import time
import cStringIO
import urllib
from PIL import Image, ImageTk

class ImageModule(JSONParentPoller,threading.Thread):
    def __init__(self):
        super(ImageModule, self).__init__()
        self.daemon=True
        self.fsg=musicazoo.lib.graphics.FullScreenGraphics()
        self.fsg.sync(self.start)
        self.fsg.run()
        self.shutdown()

    def shutdown(self):
        self.running=False
        self.rm()
        self.close()
        self.join()

    def load(self):
        self.set_parameters({"url": self.url})
        f = cStringIO.StringIO(urllib.urlopen(self.url).read())
        i=Image.open(f)
        self.pi_seq=[]
        self.image_seq=[]
        try:
            while True:
                i.thumbnail((self.fsg.width,self.fsg.height),Image.ANTIALIAS)
                if 'duration' in i.info:
                    duration=i.info['duration']
                else:
                    duration=100
                self.image_seq.append(i.copy())
                self.pi_seq.append((ImageTk.PhotoImage(i, master=self.fsg),duration))
                i.seek(len(self.image_seq))
        except EOFError:
            pass

        if len(self.pi_seq) == 0:
            raise Exception("Bad image file.")

        if len(self.pi_seq) > 1:
            def flip(i):
                img,dur=self.pi_seq[i]
                self.c.itemconfig(self.tkimg,image=img)
                self.fsg.after(dur,lambda:flip((i+1)%len(self.pi_seq)))
            flip(0)
        else:
            img,dur=self.pi_seq[0]
            self.c.itemconfig(self.tkimg,image=img)

    def cmd_init(self,url,bg=sets.bg_color):
        self.set_parameters({
            "url":url,
            "bg":bg,
        })

        self.url=url

        self.c=Tkinter.Canvas(self.fsg,width=self.fsg.width,height=self.fsg.height,highlightthickness=0,bg=bg)
        self.tkimg=self.c.create_image(*self.fsg.center())

        self.c.pack()
        self.fsg.sync(self.load)

    def cmd_rm(self):
        self.fsg.sync(self.fsg.over)
        self.running=False

    def cmd_play(self):
        self.fsg.sync(self.fsg.show)

    def cmd_suspend(self):
        self.fsg.sync(self.fsg.hide)

    def run(self):
        self.running=True
        try:
            while self.running:
                self.handle_one_command()
        except socket.error:
            if self.running:
                self.fsg.sync(self.fsg.over)
                raise

    commands = {
        'init':cmd_init,
        'rm':cmd_rm,
        'play':cmd_play,
        'suspend':cmd_suspend,
    }

mod = ImageModule()

