from shmooze.modules import JSONParentPoller
import shmooze.settings as sets
import musicazoo.lib.graphics
import threading
import socket
import Tkinter
import time

class TextBGModule(JSONParentPoller,threading.Thread):
    def __init__(self):
        super(TextBGModule, self).__init__()
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

    def cmd_init(self,text,bg=sets.bg_color,fg=sets.fg_color,font="Helvetica",size=72):
        self.set_parameters({
            "text":text,
            "bg":bg,
            "fg":fg,
            "font":font,
            "size":size,
        })

        c=Tkinter.Canvas(self.fsg,width=self.fsg.width,height=self.fsg.height,highlightthickness=0,bg=bg)
        c.pack()

        coord = self.fsg.center()
        arc = c.create_text(coord, text=text, fill=fg, justify=Tkinter.CENTER, font=(font,size))

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

mod = TextBGModule()

