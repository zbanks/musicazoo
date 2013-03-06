from musicazooTemplates import MusicazooShellCommandModule

from subprocess import Popen, PIPE
import re
import urlparse
import os

null_f = open("/dev/null", "rw")


class MPlayer(MusicazooShellCommandModule):
    resources = ("audio", "screen")
    persistent = False
    keywords = ()
    duration = 0
    command = ("mplayer","-framedrop","-cache","8192","-vo","xv", "-fs","-slave")
    button_list = {"pause" : "pause",
                   "pausing_keep seek 0 1" : "restart"}


    def __init__(self, json):
        # Call musicazoo shell command initializer 
        self._initialize(json)

        # Initialize module parameters
        self.filepath = json["arg"].strip().split(" ")[-1]
#self.status_dict = {"url": self.url}
        self.status_dict = {}


    """
    def _gettitle(self):
        self.title = "%s" % (entry.media.title.text)
        self.queue_html = "<a href='%s'>%s</a> [%s]" % (self.url, self.title, self.duration)
        self.playing_html = "<a href='%s'>%s</a> [%s]" % (self.url, self.title, self.duration) 

    """
    title = "(Upload)"
    queue_html = "(Upload)"
    playing_html = "(Upload)"

    def message(self, json):
        if self.subprocess:
            if "command" in json:
                if json["command"] in self.button_list:
                    self.subprocess.stdin.write(json["command"]+"\n")

    def _run(self,cb):
        dl_cmd = self.command + (self.filepath.encode('ascii'),)
        
        mplayer_env = os.environ.copy()
        mplayer_env["DISPLAY"]=":0"
        mplayer = Popen(dl_cmd, stderr=null_f, stdout=PIPE, stdin=PIPE, env=mplayer_env)
        self.subprocess = mplayer
        print "Running youtube"

        button_template = "<a class='rm button' href='/msg?for_id=%s&command=%%s'>%%s</a>" % self.id
        buttons = "\n".join(map(lambda x: button_template % x, self.button_list.items()))
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
