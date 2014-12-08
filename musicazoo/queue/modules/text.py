from musicazoo.queue import pymodule
import musicazoo.lib.graphics
import threading
import socket
import Tkinter
import time

class TextModule(pymodule.JSONParentPoller,threading.Thread):
    def __init__(self):
        super(TextModule, self).__init__()
        self.daemon=True
        self.fsg=musicazoo.lib.graphics.FullScreenGraphics()
        self.fsg.sync(self.start)
        self.fsg.run()
        self.shutdown()

    def shutdown(self):
        self.running=False
        self.connection.send_update({"cmd":"rm"})
        self.close()
        self.join()

    def cmd_init(self,text,duration=0):
        c=Tkinter.Canvas(self.fsg,width=self.fsg.width,height=self.fsg.height,highlightthickness=0,bg="black")
        c.pack()

        coord = self.fsg.center()
        arc = c.create_text(coord, text=text, fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))
        self.remaining_time=duration

    def cmd_rm(self):
        self.fsg.sync(self.fsg.over)
        self.running=False

    def cmd_play(self):
        self.fsg.sync(self.fsg.show)
        self.fsg.after(int(self.remaining_time*1000),self.fsg.over)
        self.start_time=time.time()

    def cmd_suspend(self):
        self.fsg.sync(self.fsg.hide)
        self.remaining_time=self.start_time-time.time()
        if self.remaining_time <= 0:
            self.fsg.sync(self.fsg.over)

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

mod = TextModule()

