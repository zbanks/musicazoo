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
    command = ("/usr/local/bin/mplayer","-framedrop","-cache","8192","-cache-min", "10","-vo","xv", "-fs","-slave")
    duration = 0
    url = ""
    button_list = [("pause", "pause"),
                   ("pausing_keep seek 0 1", "restart"),
#("speed_set -1.0", "rev"),
                   ("speed_set 0.67", "slow"),
                   ("speed_set 1", "normal speed"),
                   ("speed_set 1.33", "fast" ),
                   ("seek 30 0", "+0:30"),
                   ("seek -30 0", "-0:30")
#                   ("speed_set 2.5", "ffwd")
                  ]
    button_dict = dict(button_list)
    button_regexes = [ # Be fucking careful with these regexes. FUCKING CAREFUL
                   r"speed_set -?[0-5]([.][0-9]{1,3})?",
                   r"seek [0-9]{1,5}( [012])?"
                   ]


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
                if json["command"] not in self.button_dict:
                    for bregex in self.button_regexes:
                        if re.match(bregex, json["command"]):
                            break
                    else:
                        return
                self.subprocess.stdin.write(json["command"]+"\n")

    def _run(self,cb):
        dl_cmd = self.command + (self.filepath.encode('ascii'),)
        
        mplayer_env = os.environ.copy()
        mplayer_env["DISPLAY"]=":0"
        mplayer = Popen(dl_cmd, stderr=null_f, stdout=PIPE, stdin=PIPE, env=mplayer_env)
        self.subprocess = mplayer

        button_template = "<a class='rm button' href='/msg?for_id=%s&command=%%s'>%%s</a>" % self.id
        buttons = "\n".join(map(lambda x: button_template % x, self.button_list))
        self.timein = "0:00"
        self.seconds = 0

        if not self.duration:
            self.subprocess.stdin.write("get_time_length\n")

        # Loop continuously, getting output and setting titles
        while self.subprocess.poll() == None:
            out = self.subprocess.stdout.readline(100)
#print out
            match = re.search(r'A:\s*(\d+)[.]\d+', out)
            if match:
                self.seconds = int(match.group(1))
                self.timein = "%d:%02d" % (self.seconds / 60, self.seconds % 60)

            if out[:3] == "ANS":
                key, arg = out.split("=")
                if key == "ANS_LENGTH":
                    self.duration = int(arg.strip())

            if self.duration and self.url:
                self.playing_html = "<a href='%s'>%s</a> [%s/%s] %s <span class='ytprogress'></span>" % (self.url, self.title, self.timein, self.duration, buttons) 
            else:
                self.playing_html = "%s [%s] %s" % (self.title, self.timein, buttons) 
        cb()
