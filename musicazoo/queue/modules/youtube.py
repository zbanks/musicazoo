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
            "url", "title", "duration", "site", "media", "thumbnail", "description",
            "time", "status"
            ]
        }
        return result

    def cmd_init(self, url):
        print "URL:", url
        self.player=Player()
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
        self.status='added'
        messages.put("init")
        self.update()
        return packet.good()

    def cmd_play(self):
        print "Play"
        messages.put("play")
        return packet.good()

    def cmd_suspend(self):
        print "Suspend"
        self.player.pause()
        self.update()
        return packet.good()

    def cmd_rm(self):
        print "Remove"
        self.player.stop()
        messages.put("rm")
        self.update()
        messages.join()
        return packet.good()

    def cmd_seek_abs(self, position):
        if not self.player.up():
            raise Exception("Video is not up")
        self.player.seek_abs(position)
        return packet.good()

    def cmd_seek_rel(self, time):
        if not self.player.up():
            raise Exception("Video is not up")
        self.player.seek_rel(position)
        return packet.good()

    def play(self):
        self.player.load(self.media,cookies=self.cookies)
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

        if self.status=='added':
            self.status='ready'

        self.update()
        return True

    commands={
        'init':cmd_init,
        'play':cmd_play,
        'suspend':cmd_suspend,
        'rm':cmd_rm,
        'pause': cmd_suspend,
        #'resume': resume,
        #'set_rate': cmd_set_rate,
        'seek_rel': cmd_seek_rel,
        'seek_abs': cmd_seek_abs,
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
