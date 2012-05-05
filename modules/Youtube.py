from musicazooTemplates import MusicazooShellCommandModule

import gdata.youtube.service as yt
import re
import urlparse

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
    command = ("/usr/local/bin/playyoutube",)

    @staticmethod
    def match(input_str):
        return not not re.search("http.+www\.youtube\.com/watch.+v", input_str.strip())

    def __init__(self, json):
        # Call musicazoo shell command initializer 
        self._initialize(json)

        # Initialize module parameters
        self.url = json["arg"].strip().split(" ")[-1]
        self.command += (self.url,)

        self.status_dict = {"url": self.url}

        # Get title of youtube video
        self._gettitle()

    def _gettitle(self):
        yt_service = yt.YouTubeService()
        entry = yt_service.GetYouTubeVideoEntry(video_id=getYouTubeIdFromUrl(self.url))
        self.title = entry.media.title.text
        self.queue_html = "<a href='%s'>%s</a>" % (self.url, self.title)
        self.playing_html = "<a href='%s'>%s</a>" % (self.url, self.title) 
