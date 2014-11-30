if __name__ != '__main__':
    # If name is not main then this was imported for use in the queue process

    import musicazoo.queue.module as module

    class Youtube(module.Module):
        TYPE_STRING='youtube'
        process = ['python',__file__] # The sub-process to execute is itself
        # tell me that isn't cute
else:
    # If name is main then this is the sub-process
    # admittedly, it does feel very fork-esque
    import os
    import tempfile
    import time
    import youtube_dl 

    import musicazoo.lib.packet as packet
    import musicazoo.queue.pymodule as pymodule

    from youtube_dl.compat import compat_cookiejar, compat_urllib_request
    from youtube_dl.utils import make_HTTPS_handler, YoutubeDLHandler
    from musicazoo.lib.vlc_player_compat import Player

    from musicazoo.lib.watch_dl import WatchCartoonOnlineIE

    class YoutubeModule(pymodule.JSONParentPoller):
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
            self.getVideoInfo()
            return packet.good()

        def cmd_play(self):
            print "Play"
            self.player.load(self.media,cookies=self.cookies)
            return packet.good()

        def cmd_suspend(self):
            print "Suspend"
            self.player.stop()

        def getVideoInfo(self):
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

            return True

    mod = YoutubeModule()

    import sys
    import threading

    t=threading.Thread(target=mod.poller)
    t.daemon=True
    t.start()

    import time
    while True:
        time.sleep(1)
    
    print "QUITTING"
    mod._close()
