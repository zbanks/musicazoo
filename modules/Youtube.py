from musicazooTemplates import MusicazooShellCommandModule

import gdata.youtube.service as yt
import re

def getYouTubeIdFromUrl(url):
    try:
        return re.search(r"&v=(.*)$",url).group(1)
    except:
        #FIXME: I think this is funny. You may not.
        return "C_S5cXbXe-4" 

class Youtube(MusicazooShellCommandModule):
    resources = ("audio", "screen")
    persistent = False
    keywords = ("youtube", "yt")
    command = ("playyoutube",)

    def __init__(self, json):
        # Call musicazoo shell command initializer 
        self.__initialize(json)

        # Initialize module parameters
        self.url = json["arg"]
        self.command += (self.url,)

        # Get title of youtube video
        self.__gettitle()

    def __gettitle(self):
        yt_service = yt.YouTubeService()
        entry = yt_service.GetYouTubeVideoEntry(video_id=getYouTubeIdFromUrl(self.url))
        self.title = entry.media.title.text
