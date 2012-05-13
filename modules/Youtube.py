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
    command = ("mplayer","-framedrop","-cache","8192","-vo","xv",
               "-fs","-cookies","-cookies-file",cookie_file)

    @staticmethod
    def match(input_str):
        return not not re.search("http.+www\.youtube\.com/watch.+v", input_str.strip())

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
                self.subprocess.stdin.write(json["command"]+"\n")

    def _run(self,cb):
        youtube_dl = Popen(("youtube-dl","-g","--max-quality=18","--cookies", cookie_file, self.url),
                           stderr=null_f, stdin=null_f, stdout=PIPE)
        dl_cmd = self.command + (youtube_dl.stdout.readline().strip(),)
        
        mplayer_env = os.environ.copy()
        mplayer_env["DISPLAY"]=":0"
        mplayer = Popen(dl_cmd, stderr=null_f, stdout=PIPE, stdin=PIPE, env=mplayer_env)
        self.subprocess = mplayer
        print "Running youtube"

        button_template = "<a class='rm button' href='/msg?for_id=%s&command=%%s'>%%s</a>" % self.id
        button_list = {"pause" : "pause",}
        buttons = "\n".join(map(lambda x: button_template % x, button_list.items()))
        self.timein = "0:00"
        self.seconds = 0

        # Loop continuously, getting output and setting titles
        while self.subprocess.poll() == None:
            out = self.subprocess.stdout.readline(100)
            print out
            match = re.search(r'V:\s*(\d+)[.]\d+', out)
            if match:
                self.seconds = int(match.group(1))
                self.timein = "%d:%02d" % (self.seconds / 60, self.seconds % 60)
            self.playing_html = "<a href='%s'>%s</a> [%s/%s] %s" % (self.url, self.title, self.timein, self.duration, buttons) 
        cb()
