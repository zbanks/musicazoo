from musicazooTemplates import MusicazooShellCommandModule

from subprocess import Popen, PIPE
import gdata.youtube.service as yt
import re
import urlparse
import os

null_f = open("/dev/null", "rw")
cookie_file="/var/tmp/youtube-dl-cookies.txt"

def getYouTubeIdFromUrl(url):
    try:
        params = urlparse.urlparse(url).query
        return urlparse.parse_qs(params)["v"][0]
    except Exception as err:
        #FIXME: I think this is funny. You may not.
        return "C_S5cXbXe-4" 

class Youtube(MusicazooShellCommandModule):
    resources = ("audio", "screen")
    persistent = False
    keywords = ("youtube", "yt")
    duration = 0
    command = ("/usr/local/bin/mplayer","-framedrop","-cache","8192","-cache-min", "10","-vo","xv",
               "-fs","-slave","-cookies","-cookies-file",cookie_file)
    button_list = [("pause", "pause"),
                   ("pausing_keep seek 0 1", "restart"),
#("speed_set -1.0", "rev"),
                   ("speed_set 0.67", "slow"),
                   ("speed_set 1", "normal speed"),
                   ("speed_set 1.33", "fast" ),
#                   ("speed_set 2.5", "ffwd")
                  ]
    button_dict = dict(button_list)
    button_regexes = [ # BE FUCKING CAREFUL WITH THESE REGEXES
                   r"speed_set -?[0-5]([.][0-9]{1,3})?",
                   r"seek [0-9]{1,5}( [012])?"
                   ]

    @staticmethod
    def match(input_str):
        return None
        if re.search("http.+www\.youtube\.com/watch.+v", input_str.strip()):
            return input_str

    def __init__(self, json):
        # Call musicazoo shell command initializer 
        self._initialize(json)

        # Initialize module parameters
        self.url = json["arg"].strip().split(" ")[-1]
        self.status_dict = {"url": self.url}

        # Get title of youtube video
        self._gettitle()

    def _gettitle(self):
        yt_service = yt.YouTubeService()
        entry = yt_service.GetYouTubeVideoEntry(video_id=getYouTubeIdFromUrl(self.url))
        seconds = int(entry.media.duration.seconds)
        self.duration = "%d:%02d" % (seconds / 60, seconds % 60)
    
        self.title = "%s" % (entry.media.title.text)
        self.queue_html = "<a href='%s'>%s</a> [%s]" % (self.url, self.title, self.duration)
        self.playing_html = "<a href='%s'>%s</a> [%s]" % (self.url, self.title, self.duration) 

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
        youtube_dl = Popen(("youtube-dl","-g","--max-quality=18","--cookies", cookie_file, self.url),
                           stderr=null_f, stdin=null_f, stdout=PIPE)
        self.subprocess = youtube_dl # Temporarily make subprocess youtube_dl
        dl_cmd = self.command + (youtube_dl.stdout.readline().strip(),)
        
        if not self.running:
            # Killed, stop!
            cb()
            return
        mplayer_env = os.environ.copy()
        mplayer_env["DISPLAY"]=":0"
        mplayer = Popen(dl_cmd, stderr=null_f, stdout=PIPE, stdin=PIPE, env=mplayer_env)
        self.subprocess = mplayer
        print "Running youtube"

        button_template = "<a class='rm button' href='/msg?for_id=%s&command=%%s'>%%s</a>" % self.id
        buttons = "\n".join(map(lambda x: button_template % x, self.button_list))
        self.timein = "0:00"
        self.seconds = 0

        # Loop continuously, getting output and setting titles
        while self.subprocess.poll() == None and self.running:
            out = self.subprocess.stdout.readline(100)
#print out
            match = re.search(r'V:\s*(\d+)[.]\d+', out)
            if match:
                self.seconds = int(match.group(1))
                self.timein = "%d:%02d" % (self.seconds / 60, self.seconds % 60)
            self.playing_html = "<a href='%s'>%s</a> [%s/%s] %s <span class='ytprogress'></span>" % (self.url, self.title, self.timein, self.duration, buttons) 
        cb()
