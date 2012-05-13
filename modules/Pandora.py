from musicazooTemplates import MusicazooShellCommandModule
from subprocess import Popen, PIPE
import time
import re

null_f = open("/dev/null", "rw")

class Pandora(MusicazooShellCommandModule):
    resources = ("audio",)
    persistent = True
    keywords = ("pandora","pd")
    command = ("pianobar",)
    title = "Pandora"
    queue_html = "Pandora"
    playing_html = "Pandora"

    email = "musicazoo@mit.edu"
    password = "musicazoo"
    newsongf = None
    
    def __init__(self,json):
        self._initialize(json)

    def run(self,cb,newsongf=None):
        self.newsongf = newsongf # Function to run every time a song changes
#self._run(cb)
        super(Pandora, self).run(cb)
        
    def pause(self, cb):
        self.message({"command":"p"})
        cb()
    
    def unpause(self, cb):
        self.message({"command":"p"})
        cb()

    def message(self,json):
        if self.subprocess:
            if "command" in json:
                self.subprocess.stdin.write(json["command"])


    def _run(self,cb):
        command = self.command
        self.subprocess = Popen(command, stderr=null_f, stdout=PIPE, stdin=PIPE)
        self.subprocess.stdin.write("%s\n" % self.email)
        self.subprocess.stdin.write("%s\n" % self.password)
        self.subprocess.stdin.write("0\n")

        button_template = "<a class='rm button' href='/msg?for_id=%s&command=%%s'>%%s</a>" % self.id
        button_list = {"p" : "p",
                       "n" : "skip",
                       "+" : "+"
#"-" : "-" 
                      }
        buttons = "\n".join(map(lambda x: button_template % x, button_list.items()))
        self.song_title = ""
        self.song_time = ""

        # Loop continuously, getting output and setting titles
        while self.subprocess.poll() == None:
            out = self.subprocess.stdout.readline();
            print out
            match = re.search(r'[|]>\s*(".*)\s*@[^@]*$', out)
            if match: 
                self.song_title = match.group(1)
                if self.newsongf:
                    newsongf()
            match_time = re.search(r'#\s*Time:(-?\d+:\d+/\d+:\d+)', out)
            if match_time:
                self.song_time = match_time.group(1)

            self.title = "Pandora: %s [%s]" % (self.song_title, self.song_time)
            self.playing_html = "%s %s" % (self.title, buttons)
        cb()
        
