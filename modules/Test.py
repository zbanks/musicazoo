from musicazooTemplates import MusicazooShellCommandModule

import re

class Test(MusicazooShellCommandModule):
    resources = ("screen")
    persistent = False
    keywords = ("msg")
    command = ("tail -f /dev/null",)

    def __init__(self, json):
        # Call musicazoo shell command initializer 
        self._initialize(json)

        # Initialize module parameters
        self.m = json["arg"]

        self.status_dict = {"m": self.m}
        self.title = "Test: %s" % self.m
        self.queue_html = self.title
        self.playing_html = self.title + " - Playing"

        # Get title of youtube video

    def message(self, json):
        if "m" in json:
            self.m = json["m"]
        self.title = "Test: %s" % self.m
        self.queue_html = self.title
        self.playing_html = self.title + " - Playing"
