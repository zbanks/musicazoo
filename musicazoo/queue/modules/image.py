from musicazoo.queue import pymodule
import musicazoo.lib.graphics
import musicazoo.settings as sets
import threading
import socket
import Tkinter
import time
import cStringIO
import urllib
from PIL import Image, ImageTk

class ImageModule(pymodule.JSONParentPoller,threading.Thread):
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
        f = cStringIO.StringIO(urllib.urlopen(self.url).read())
        i=Image.open(f)
        i.thumbnail((self.fsg.width,self.fsg.height),Image.ANTIALIAS)
        self.image=ImageTk.PhotoImage(i, master=self.fsg)
        self.c.itemconfig(self.tkimg,image=self.image)

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

