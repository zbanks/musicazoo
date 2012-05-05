from musicazooTemplates import MusicazooShellCommandModule

import re

class Volume(MusicazooShellCommandModule):
    resources = ()
    persistent = False
    keywords = ("vol",)
    command = ("/usr/bin/amixer","-q","set","PCM")

    def __init__(self, json):
        # Call musicazoo shell command initializer 
        self._initialize(json)

        # Initialize module parameters
        raw_vol = int(json["arg"].strip())
        vol = "%d%%" % max(min(raw_vol, 100), 0)
        self.command += (vol,)        
        print self.command

        self.status_dict = {"vol": raw_vol}
        self.title = "(Set volume: %s)" % vol
        self.queue_html = self.title
        self.playing_html = self.title

