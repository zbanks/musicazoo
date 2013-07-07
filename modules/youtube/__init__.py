import time

import youtube_dl
from youtube_dl.utils import *
import vlc
import threading

class Youtube:
	TYPE_STRING='youtube'

	def __init__(self,url):
		self.url=url
		self.title=None
		self.duration=None
		self.site=None
		self.media=None
		self.status='added'
		t=threading.Thread(target=self.getVideoInfo, args=(url))
		t.daemon=True
		t.start()

	def get_url(self):
		return self.url

	def play(self):
		self.status='loading'
		self.getVideoInfo(self.url)
		self.vlcPlay()
		self.status='finishing'

	def pause(self):
		pass

	def vlcPlay(self):
		os.environ["DISPLAY"] = ":0"
		self.vlc_i = vlc.Instance('--fullscreen')
		self.vlc_mp = self.vlc_i.media_player_new()
		media = self.vlc_i.media_new(self.media)
		self.vlc_mp.set_media(media)
		self.vlc_mp.set_fullscreen(True)

		self.status='playing'
		self.vlc_mp.play()

		'''
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
		'''

		# Loop continuously, getting output and setting titles
		while self.vlc_mp.get_state() != vlc.State.Ended :
			time.sleep(0.5)

			'''		    
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
			'''

	# Class variables

	commands={
		'pause':pause
	}

	parameters={
		'url':get_url
	}

	# Low-level stuff.
	def getVideoInfo(self,url):
		# General configuration
		cookie_file="yt-cookies"
		jar = compat_cookiejar.MozillaCookieJar(cookie_file)
		if os.access(cookie_file, os.R_OK):
			jar.load()
		cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
		proxies = compat_urllib_request.getproxies()
		proxy_handler = compat_urllib_request.ProxyHandler(proxies)
		https_handler = make_HTTPS_handler(None)
		opener = compat_urllib_request.build_opener(https_handler, proxy_handler, cookie_processor, YoutubeDLHandler())
		compat_urllib_request.install_opener(opener)
		socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

		y=youtube_dl.YoutubeDL({'outtmpl':''}) # empty outtmpl needed due to weird issue in youtube-dl
		y.add_default_info_extractors()
		info=y.extract_info(url,download=False)

		self.title=info['entries'][0]['title']
		self.duration=info['entries'][0]['duration']
		self.site=info['entries'][0]['extractor']
		self.media=info['entries'][0]['url']
		self.status='ready'

if __name__=='__main__':
	m=YoutubeModule("http://www.youtube.com/watch?v=F57P9C4SAW4")
	m.play()
