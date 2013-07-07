from subprocess import Popen, PIPE
from threading import Thread
from time import sleep

import os
import re
import time
import urlparse
import vlc

null_f = open("/dev/null", "rw")

class VLC(object):
    resources = ('audio', 'screen')
    persistent = False
    keywords = ('vlc')
    catchall = False 
    command = ()
    title = '(VLC)'
    status_dict = {}
    queue_html = None
    playing_html = None
    running = False
    loaded = False
    duration = 0
    url = ""
    killed = False
    vlc_i = None
    button_list = [("pause", "pause"),
                   ("pausing_keep seek 0 1", "restart"),
                   ("speed_set 0.67", "slow"),
                   ("speed_set 1", "normal speed"),
                   ("speed_set 1.33", "fast" ),
                   ("seek 30 0", "+0:30"),
                   ("seek -30 0", "-0:30")
                  ]
    
    @staticmethod
    def match(input_str):
        return False

    def __init__(self, json):
        self.status_dict = {} #possibly causing issues? 
        self._initialize(json)
        self.filepath = json["arg"]
        self.title = "(VLC)"

    def _initialize(self, json):
        self.json = json
        self.id = json["id"]
        self.thread = None

    def run(self, cb):
        # setup a thread to run the shell command
#command = self.command
#self.subprocess = popen(command, shell=false, stderr=null_f, stdout=null_f, stdin=pipe)
        self.running = True
        self.thread = Thread(target=self._run, 
                             name="musicazoo-%s"%self.id,
                             args=(cb,))
        self.thread.daemon = True
        self.thread.start()
            
    def pause(self, cb):
        self.kill()
        self.running = False
        cb()

    def unpause(self, cb):
        self.run(cb)

    def kill(self):
        if self.vlc_i:
            self.vlc_mp.stop()
            self.vlc_i.release()
        self.running = False
        self.killed = True

    def status(self):
        output = self.status_dict
        output["running"] = self.running
        output["id"] = self.id
        output["resources"] = self.resources
        output["persistent"] = self.persistent  # we do not want to be persistent
        output["title"] = self.title
        output["queue_html"] = self.queue_html
        output["playing_html"] = self.playing_html

        if not self.queue_html:
            output["queue_html"] = self.title
        if not self.playing_html:
            output["playing_html"] = self.title
        return output
    
    def message(self,json):
        pass

    def _run(self,cb):
        os.environ["DISPLAY"] = ":0"
        self.vlc_i = vlc.Instance('--fullscreen')
        self.vlc_mp = self.vlc_i.media_player_new()
        media = self.vlc_i.media_new(self.filepath)
        self.vlc_mp.set_media(media)
        self.vlc_mp.set_fullscreen(True)

        print "Loaded, playing", self.duration
        self.vlc_mp.play()

        button_template = "<a class='rm button' href='/msg?for_id=%s&command=%%s'>%%s</a>" % self.id
        buttons = "\n".join(map(lambda x: button_template % x, self.button_list))
        self.timein = "0:00"
        self.seconds = 0

        if not self.duration:
            for i in range(10):
                self.duration = self.vlc_mp.get_length() / 1000
                if self.duration != -1:
                    self.loaded = True
                    break
                print 'waiting for dir'
                time.sleep(0.2)
            else:
                self.duration = 0
        print 'dur', self.duration
        timeat = lambda x: "%d:%02d" % (x / 60, x % 60)

        # Loop continuously, getting output and setting titles
        while not self.killed and  self.vlc_mp.get_state() != vlc.State.Ended :
            time.sleep(0.5)
            
            self.seconds = self.vlc_mp.get_time() / 1000
            self.duration = max(self.vlc_mp.get_length() / 1000, self.duration)
            if self.seconds == -1:
                self.seconds = 0
                self.loaded = False
            else:
                self.loaded = True

            if self.url:
                self.playing_html = "VLC - <a href='%s'>%s</a> [%s/%s] %s <span class='ytprogress'></span>" % (self.url, self.title, timeat(self.seconds), timeat(self.duration), buttons) 
            else:
                self.playing_html = "VLC - %s [%s:%s] %s" % (self.title, timeat(self.seconds), timeat(self.duration), buttons) 
        cb()
        
