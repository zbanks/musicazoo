import os
import socket
import tempfile
import time
import youtube_dl 
import Queue

import shmooze.lib.packet as packet
import musicazoo.lib.vlc as vlc
from shmooze.modules import JSONParentPoller

from musicazoo.lib.watch_dl import WatchCartoonOnlineIE

from youtube_dl.compat import compat_cookiejar, compat_urllib_request
from youtube_dl.utils import make_HTTPS_handler, YoutubeDLHandler

import threading
import urllib2

messages = Queue.Queue()

def get_mime_type(url):
    class HeadRequest(urllib2.Request):
        def get_method(self):
            return "HEAD"
    try:
        response = urllib2.urlopen(HeadRequest(url))
        return response.info().dict['content-type']
    except Exception as e:
        raise Exception("URL Error")

class YoutubeModule(JSONParentPoller):
    def __init__(self, headless=False):
        self.headless=headless
        self.update_lock = threading.Lock() # TODO I don't think this needs to exist
        self.thread_stopped = False 
        super(YoutubeModule, self).__init__()

    def serialize(self):
        result = { t: getattr(self, t) for t in [
            "url", "title", "duration", "site", "media", "thumbnail", "description", "time", "vid"
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
        return result

    @property
    def state_is_playing(self):
        return self.state_has_started and not (self.state_is_suspended or self.state_is_paused)

    def cmd_init(self, url):
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
        self.safe_update()

    def hide(self):
        self.vlc_mp.video_set_track(-1)

    def show(self):
        self.vlc_mp.video_set_track(0)

    def cmd_play(self):
        if self.state_has_started:
            if not self.state_is_paused:
                self.vlc_mp.play()
                self.show()
                self.state_is_paused = False
        else:
            messages.put("play")
        self.state_is_suspended = False
        self.safe_update()

    def cmd_suspend(self):
        if self.state_has_started:
            if self.vlc_mp.is_playing():
                self.vlc_mp.pause()
                self.hide()
            #self.state_is_paused = True
        self.state_is_suspended = True
        self.safe_update()

    def cmd_resume(self):
        if self.state_has_started:
            self.vlc_mp.play()
            self.state_is_paused = False
            self.safe_update()

    def cmd_pause(self):
        if self.state_has_started:
            if self.vlc_mp.is_playing():
                self.vlc_mp.pause()
            self.state_is_paused = True
            self.safe_update()

    def cmd_rm(self):
        self.state_is_stopping = True
        messages.put("rm")
        #messages.join()

    def cmd_seek_abs(self, position):
        #TODO: if the video hasn't started, then cache the position and set it as soon as the video starts
        if self.state_has_started:
            self.vlc_mp.set_time(int(position*1000))
            self.time = position
            self.safe_update()

    def cmd_seek_rel(self, delta):
        if self.state_has_started:
            cur_time = self.vlc_mp.get_time()
            if cur_time < 0:
                return
            self.vlc_mp.set_time(cur_time+int(delta*1000))
            self.time = (cur_time / 1000) + delta
            self.safe_update()

    def stop(self):
        self.vlc_mp.stop()
        self.thread_stopped = True

        with self.update_lock:
            self.rm()

    def play(self):
        def ev_end(ev):
            messages.put("rm")

        def ev_time(ev):
            self.time = ev.u.new_time / 1000.
            self.safe_update()

        def ev_length(ev):
            self.duration = ev.u.new_length / 1000.
            self.safe_update()

        if not self.headless:
            #os.environ["DISPLAY"] = ":0"
            self.vlc_i = vlc.Instance(['--no-video-title-show']) # -f
        else:
            self.vlc_i = vlc.Instance(['--novideo'])
        self.vlc_mp = self.vlc_i.media_player_new()
        self.vlc_ev = self.vlc_mp.event_manager()

        self.vlc_ev.event_attach(vlc.EventType.MediaPlayerEndReached, ev_end)
        self.vlc_ev.event_attach(vlc.EventType.MediaPlayerTimeChanged, ev_time)
        self.vlc_ev.event_attach(vlc.EventType.MediaPlayerLengthChanged, ev_length)

        vlc_media=self.vlc_i.media_new_location(self.media)
        self.vlc_mp.set_media(vlc_media)
        self.vlc_mp.play()

        self.state_has_started = True
        self.safe_update()

    def get_video_info(self):
        url = self.url
        mimetype=get_mime_type(url)

        if mimetype.startswith("text/html"):
            params={}
            # General configuration
            tf=tempfile.NamedTemporaryFile(delete=False)
            tf.close()
            self.cookies=tf.name
            jar = compat_cookiejar.MozillaCookieJar(self.cookies)
            cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
            proxies = compat_urllib_request.getproxies()
            proxy_handler = compat_urllib_request.ProxyHandler(proxies)
            https_handler = make_HTTPS_handler(params)
            ydlh = YoutubeDLHandler(params)
            opener = compat_urllib_request.build_opener(https_handler, proxy_handler, cookie_processor, ydlh)
            compat_urllib_request.install_opener(opener)

            y=youtube_dl.YoutubeDL({'outtmpl':u'','skip_download':True}, auto_init=False) # empty outtmpl needed due to weird issue in youtube-dl
            y.add_info_extractor(WatchCartoonOnlineIE())
            y.add_default_info_extractors()

            try:
                info=y.extract_info(url,download=False)
            except Exception:
                raise
                self.status='invalid'
                self.queue.removeMeAsync(self.uid) # Remove if possible # TODO error here
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

        else:
            self.media=url
            self.title=url

        self.state_is_ready = True
        self.safe_update()
        return True

    # TODO This shouldn't exist.
    def safe_update(self):
        with self.update_lock:
            self.set_parameters(self.serialize())

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

import sys

headless = '--headless' in sys.argv

mod = YoutubeModule(headless=headless)

def serve_forever():
    while not mod.thread_stopped:
        try:
            mod.handle_one_command()
        except socket.error:
            break

t=threading.Thread(target=serve_forever)
t.daemon=True
t.start()

while True:
    msg = messages.get(block=True)
    messages.task_done()
    if msg == "init":
        mod.get_video_info()
    elif msg == "play":
        mod.play()
    elif msg == "rm":
        mod.stop()
        break
    
mod.close()
