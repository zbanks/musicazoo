import os
import tempfile
import time
import youtube_dl 
import Queue

import musicazoo.lib.packet as packet
import musicazoo.queue.pymodule as pymodule

from youtube_dl.compat import compat_cookiejar, compat_urllib_request
from youtube_dl.utils import make_HTTPS_handler, YoutubeDLHandler
from musicazoo.lib.vlc_player_compat import Player

from musicazoo.lib.watch_dl import WatchCartoonOnlineIE

messages = Queue.Queue()

class YoutubeModule(pymodule.JSONParentPoller):
    def __init__(self):
        super(YoutubeModule, self).__init__()

    def serialize(self):
        result = { t: getattr(self, t) for t in [
            "url", "title", "duration", "site", "media", "thumbnail", "description", "time"
            ]
        }
        
        state = "initialized"
        if self.state_is_stopping:
            state = "stopping"
        elif self.state_has_started:
            if self.state_is_suspended:
                state = "suspended"
            elif self.state_is_paused:
                state = "paused"
            else:
                state = "playing"
        elif self.state_is_ready:
            state = "ready"

        result["status"] = state
        print "State:", state
        return result

    def cmd_init(self, url):
        print "URL:", url
        self.player=Player()

        # Has the youtube url/data been fetched?
        self.state_is_ready = False 
        # Has the video started playing at all?
        self.state_has_started = False
        # Is the video currently paused (by the UI)
        self.state_is_paused = False
        # Is the video currently suspended? (not at the top of the queue)
        self.state_is_suspended = False
        # Is the video stopped and currently terminating?
        self.state_is_stopping = False

        self.url=url
        self.title=None
        self.duration=None
        self.site=None
        self.media=None
        self.thumbnail=None
        self.description=None
        self.time=None
        self.vid=None
        self.cookies=None
        self.rate=None
        messages.put("init")
        self.update()
        return packet.good()

    def cmd_play(self):
        print "Play"
        if self.state_has_started:
            self.player.play()
            self.state_is_paused = False
        else:
            messages.put("play")
        self.state_is_suspended = False
        self.update()
        return packet.good()

    def cmd_suspend(self):
        print "Suspend"
        if self.state_has_started:
            self.player.pause()
        self.state_is_suspended = True
        self.update()
        return packet.good()

    def cmd_resume(self):
        print "Resume"
        if self.state_has_started:
            self.player.play()
            self.state_is_paused = False
            self.update()
        return packet.good()

    def cmd_pause(self):
        print "Pause"
        if self.state_has_started:
            self.player.pause()
            self.state_is_paused = True
            self.update()
        return packet.good()

    def cmd_rm(self):
        print "Remove"
        self.state_is_stopping = True
        self.update()

        self.player.stop()
        messages.put("rm")
        messages.join()
        return packet.good()

    def cmd_seek_abs(self, position):
        if self.player.up():
            self.player.seek_abs(position)
        return packet.good()

    def cmd_seek_rel(self, position):
        if not self.player.up():
            self.player.seek_rel(position)
        return packet.good()

    def play(self):
        self.player.load(self.media,cookies=self.cookies)
        self.state_has_started = True
        self.update()

    def get_video_info(self):
        url = self.url
        # General configuration
        tf=tempfile.NamedTemporaryFile(delete=False)
        tf.close()
        self.cookies=tf.name
        jar = compat_cookiejar.MozillaCookieJar(self.cookies)
        cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
        proxies = compat_urllib_request.getproxies()
        proxy_handler = compat_urllib_request.ProxyHandler(proxies)
        https_handler = make_HTTPS_handler(None)
        opener = compat_urllib_request.build_opener(https_handler, proxy_handler, cookie_processor, YoutubeDLHandler)
        compat_urllib_request.install_opener(opener)

        y=youtube_dl.YoutubeDL({'outtmpl':u'','skip_download':True}) # empty outtmpl needed due to weird issue in youtube-dl
        y.add_info_extractor(WatchCartoonOnlineIE())
        y.add_default_info_extractors()

        try:
            info=y.extract_info(url,download=False)
        except Exception:
            raise
            self.status='invalid'
            self.queue.removeMeAsync(self.uid) # Remove if possible
            self.ready.release()
            return False

        jar.save()

        if 'entries' in info:
            vinfo=info['entries'][0]
        else:
            vinfo=info

        if 'title' in vinfo:
            self.title=vinfo['title']
        if 'duration' in vinfo:
            self.duration=vinfo['duration']
        if 'extractor' in vinfo:
            self.site=vinfo['extractor']
        if 'url' in vinfo:
            self.media=vinfo['url']
        if 'thumbnail' in vinfo:
            self.thumbnail=vinfo['thumbnail']
        if 'description' in vinfo:
            self.description=vinfo['description']
        if 'id' in vinfo:
            self.vid=vinfo['id']

        self.state_is_ready = True
        self.update()
        return True

    commands={
        'init':cmd_init,
        'play':cmd_play,
        'suspend':cmd_suspend,
        'rm':cmd_rm,
        'do_pause': cmd_pause,
        'do_resume': cmd_resume,
        #'set_rate': cmd_set_rate,
        'do_seek_rel': cmd_seek_rel,
        'do_seek_abs': cmd_seek_abs,
    }

mod = YoutubeModule()

import sys
import threading

def serve_forever():
    while True:
        mod.handle_one_command()

t=threading.Thread(target=serve_forever)
t.daemon=True
t.start()

import time
while True:
    msg = messages.get()
    messages.task_done()
    if msg == "init":
        mod.get_video_info()
    elif msg == "play":
        mod.play()
    elif msg == "rm":
        break
    

print "QUITTING"
mod.close()
