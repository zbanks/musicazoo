from musicazooTemplates import MusicazooShellCommandModule
import re
import os
from subprocess import Popen, PIPE

null_f = open("/dev/null", "rw")

# This class is for playing music or video playlists on mplayer
class Playlist(MusicazooShellCommandModule):
    resources = ("audio",)
    persistent = True
    keywords = ("pls", "playlist")
    command = ("mplayer", "-vo", "null", "-playlist")

    @staticmethod
    def match(input_str):
        try:
            return re.search(r"^\s*(.*[.](pls|m3u|asx))\s*$", input_str.strip()).group(1)
        except Exception:
            return False
    """
    def pause(self, cb):
        self.message({"command":"pause"})
        self.kill(cb)
        cb()
    
    def unpause(self, cb):
        self.message({"command":"pause"})
        cb()
    """

    def message(self, json):
        if self.subprocess:
            if "command" in json:
                self.subprocess.stdin.write(json["command"]+"\n")

    def _run(self,cb):
        mplayer_env = os.environ.copy()
        mplayer_env["DISPLAY"]=":0"
        self.subprocess = Popen(self.command, stderr=null_f, stdout=PIPE, stdin=PIPE, env=mplayer_env)
        print "Running playlist"

        button_template = "<a class='rm button' href='/msg?for_id=%s&command=%%s'>%%s</a>" % self.id
        button_list = {"pause" : "pause",}
        buttons = "\n".join(map(lambda x: button_template % x, button_list.items()))
        self.timein = "0:00"
        self.seconds = 0

        # Loop continuously, getting output and setting titles
        while self.subprocess.poll() == None:
            out = self.subprocess.stdout.readline(100)
            print out
            match = re.search(r'A:\s*(\d+)[.]\d+', out)
            if match:
                self.seconds = int(match.group(1))
                self.timein = "%d:%02d" % (self.seconds / 60, self.seconds % 60)
            self.playing_html = "%s [%s] %s" % (self.title, self.timein, buttons) 
        cb()

