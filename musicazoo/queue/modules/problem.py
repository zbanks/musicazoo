from musicazoo.queue import pymodule
import time
import signal

def handler(signum,frame):
    print "Ignoring SIGTERM..."

class ProblematicModule(pymodule.JSONParentPoller):
    def __init__(self):
        self.run=True
        super(ProblematicModule, self).__init__()

    def cmd_init(self, noinit=False, noquit=False, noterm=False, noresponse=False, tooslow=False):
        self.noquit=noquit
        self.noresponse=noresponse
        self.tooslow=tooslow
        if noterm:
            signal.signal(signal.SIGTERM, handler)
        if noinit:
            print "Not responding to init command..."
            while True:
                time.sleep(1)

    def cmd_rm(self):
        if self.noquit:
            print "Ignoring RM message..."
        else:
            self.run=False

    def cmd_play(self):
        pass

    def do_pause(self):
        if self.tooslow:
            time.sleep(3)

    def cmd_suspend(self):
        pass

    commands = {
        'init':cmd_init,
        'rm':cmd_rm,
        'play':cmd_play,
        'suspend':cmd_suspend,
        'do_pause':do_pause
    }

mod = ProblematicModule()

while mod.run:
    mod.handle_one_command()
    if mod.noresponse:
        print "Handled init, freezing..."
        while True:
            time.sleep(1)
