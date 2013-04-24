#from MPlayer import MPlayer
from VLC import VLC

from subprocess import Popen, PIPE
import re
import urlparse
import os
import quvi

null_f = open("/dev/null", "rw")

class Video(VLC): # Internet Video
    resources = ("audio", "screen")
    persistent = False
    keywords = ("video", "vimeo")
    duration = "0:00"
#command = ("clive", "-q", "--save-dir=/tmp", "--stream-exec='mplayer %i'", "--stream=10")
    title = "Video"
    queue_html = "Video"
    playing_html = "Video"

    def __init__(self, json):
        # Call musicazoo shell command initializer 
        print json
        self._initialize(json)

        # Initialize module parameters
        self.url = json["arg"].strip().split(" ")[-1]
        self.status_dict = {"url": self.url}

        try:
            if self.get_video():
                pass   
            else:
                self.filename = "/dev/null"
        except Exception as e:
            print e

    @staticmethod
    def match(input_str):
        try:
            q = quvi.Quvi()
        except:
            print "Unable to load Quvi"
            return None
        if q.is_supported(input_str):
            return input_str

    def get_video(self):
        q = quvi.Quvi()
        if q.is_supported(self.url):
            print self.url , "supported"
            q.parse(self.url) #will throw error
            print self.url , "parsed"
            props = q.get_properties() #will throw error
            print self.url , "proped"
            seconds = int(props["mediaduration"]) / 1000
            self.filepath = props["mediaurl"]
            self.title = props["pagetitle"]
            self.url = props["pageurl"]
            self.start_time = props["starttime"]

            timeat = lambda s: "%d:%02d" % (s / 60, s % 60)
            self.duration = seconds
            self.title = "%s" % (self.title)
            self.queue_html = "VIDEO -<a href='%s'>%s</a> [%s]" % (self.url, self.title, timeat(self.duration))
            self.playing_html = "VIDEO -<a href='%s'>%s</a> [%s]" % (self.url, self.title, timeat(self.duration) )
            print self.filepath
            return True
        return False
