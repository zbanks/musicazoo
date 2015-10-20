import os
import tempfile
import time
import youtube_dl
import traceback

from shmooze.lib import service
from shmooze.modules import AsyncPyModule

from musicazoo.lib.watch_dl import WatchCartoonOnlineIE

from youtube_dl.compat import compat_cookiejar, compat_urllib_request
from youtube_dl.utils import make_HTTPS_handler, YoutubeDLHandler

import urllib2

import subprocess
import threading

def get_mime_type(url):
    class HeadRequest(urllib2.Request):
        def get_method(self):
            return "HEAD"
    try:
        response = urllib2.urlopen(HeadRequest(url))
        return response.info().dict['content-type']
    except Exception as e:
        raise Exception("URL Error")

class YoutubeModule(AsyncPyModule):
    def __init__(self, headless=False):
        self.headless=headless
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

    def check_result(self, f):
        if f.exception() is not None:
            traceback.print_exception(*f.exc_info())
            self.rm()

    @service.coroutine
    def cmd_init(self, url):
        # Has the youtube url/data been fetched?
        self.state_is_ready = False 
        # Has the video started playing at all?
        self.state_has_started = False
        # Is the video currently paused (by the UI)
        self.state_is_paused = False
        # Is the video currently suspended? (not at the top of the queue)
        self.state_is_suspended = True
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
        yield self.update()

        service.ioloop.add_future(self.async_get_video_info(), self.check_result)

    def hide(self):
        self.vlc_command("vtrack -1")

    def show(self):
        self.vlc_command("vtrack 0")

    @service.coroutine
    def cmd_play(self):
        if self.state_has_started:
            if not self.state_is_paused:
                self.vlc_command("play")
                self.show()
                self.state_is_paused = False
        else:
            yield self.play()
        self.state_is_suspended = False
        yield self.update()

    @service.coroutine
    def cmd_suspend(self):
        if self.state_has_started:
            if not self.state_is_paused:
                self.vlc_command("pause")
                self.hide()
        self.state_is_suspended = True
        yield self.update()

    @service.coroutine
    def cmd_resume(self):
        if self.state_has_started:
            self.vlc_command("play")
            self.state_is_paused = False
            yield self.update()

    @service.coroutine
    def cmd_pause(self):
        if self.state_has_started:
            if not self.state_is_paused:
                self.vlc_command("pause")
            self.state_is_paused = True
            yield self.update()

    @service.coroutine
    def cmd_rm(self):
        self.vlc_command("pause")

    @service.coroutine
    def cmd_seek_abs(self, position):
        #TODO: if the video hasn't started, then cache the position and set it as soon as the video starts
        if self.state_has_started:
            self.vlc_command("seek {0}".format(int(position)))
            self.time = position
            yield self.update()

    @service.coroutine
    def cmd_seek_rel(self, delta):
        if self.state_has_started:
            cur_time = self.vlc_command_response("get_time")
            if cur_time < 0:
                return
            self.vlc_command("seek {0}".format(cur_time + int(delta)))
            self.time = cur_time + delta
            yield self.update()

    def stop(self):
        self.is_stopping = True
        self.vlc_command("quit")
        self.vlc_process.wait()
        self.rm()

    # TODO hella refactor this
    @service.coroutine
    def play(self):
        #def ev_end(ev):
        #    messages.put("rm")

        #def ev_time(ev):
        #    self.time = ev.u.new_time / 1000.
        #    self.safe_update()

        #def ev_length(ev):
        #    self.duration = ev.u.new_length / 1000.
        #    self.safe_update()

        if not self.headless:
            #os.environ["DISPLAY"] = ":0"
            extra_args = ['--no-video-title-show']
        else:
            extra_args = ['--novideo']

        print "Popening...",self.media

        self.vlc_process = subprocess.Popen(['vlc', '-I', 'rc'] + extra_args + [self.media], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        print "Popen!"

        #self.vlc_ev.event_attach(vlc.EventType.MediaPlayerEndReached, ev_end)
        #self.vlc_ev.event_attach(vlc.EventType.MediaPlayerTimeChanged, ev_time)
        #self.vlc_ev.event_attach(vlc.EventType.MediaPlayerLengthChanged, ev_length)

        #vlc_media=self.vlc_i.media_new_location(self.media)
        #self.vlc_mp.set_media(vlc_media)
        #self.vlc_mp.play()

        self.state_has_started = True
        yield self.update()

    def vlc_command(self, cmd):
        self.vlc_process.stdin.write(cmd + '\n')
        print 'VLC CMD RESP:', self.vlc_process.stdout.read()

    def vlc_command_response(self, cmd):
        self.vlc_process.stdin.write(cmd + '\n')
        result = self.vlc_process.stdout.read()
        print 'VLC CMD RESP result:', result
        return result

    @service.coroutine
    def async_get_video_info(self):
        t = threading.Thread(target = self.get_video_info)
        t.daemon = True
        t.start()
        while t.is_alive():
            yield service.sleep(0.3)
        if not self.vid:
            raise Exception("Could not load video")

        if not self.state_is_suspended:
            yield self.cmd_play()
        else:
            yield self.update()

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

            info=y.extract_info(url,download=False)

            jar.save()

            if 'entries' in info:
                vinfo=info['entries'][0]
            else:
                vinfo=info

            print "URL",vinfo[u'url']

            # Locks? What are those?
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

        print "All ready. Media = ",self.media

        self.state_is_ready = True

    # coroutine
    def update(self):
        print "sending update..."
        return self.set_parameters(self.serialize())

    # coroutine
    def shutdown(self):
        return self.rm()

    commands={
        'init': cmd_init,
        'play': cmd_play,
        'suspend': cmd_suspend,
        'rm': cmd_rm,
        'do_pause': cmd_pause,
        'do_resume': cmd_resume,
        #'set_rate': cmd_set_rate,
        'do_seek_rel': cmd_seek_rel,
        'do_seek_abs': cmd_seek_abs,
    }

if __name__=='__main__':
    import sys
    import signal

    headless = '--headless' in sys.argv

    mod = YoutubeModule(headless = headless)

    def shutdown_handler(signum, frame):
        print
        print "Received signal, attempting graceful shutdown..."
        service.ioloop.add_callback_from_signal(mod.shutdown)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    service.ioloop.start()
