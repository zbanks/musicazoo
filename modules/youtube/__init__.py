import time

import youtube_dl
from youtube_dl.utils import *
import vlc
import threading
import os
import loading

class Youtube:
	TYPE_STRING='youtube'

	def __init__(self,queue,uid,url):
		self.queue=queue
		self.uid=uid
		self.url=url
		self.title=None
		self.duration=None
		self.site=None
		self.media=None
		self.thumbnail=None
		self.description=None
		self.time=None
		self.vid=None
		self.status='added'
		self.ready=threading.Semaphore(0)
		t=threading.Thread(target=self.getVideoInfo, args=[url])
		t.daemon=True
		t.start()

	def get_url(self):
		return self.url

	def get_title(self):
		return self.title

	def get_duration(self):
		return self.duration

	def get_site(self):
		return self.site

	def get_media(self):
		return self.media

	def get_status(self):
		return self.status

	def get_thumbnail(self):
		return self.thumbnail

	def get_description(self):
		return self.description

	def get_time(self):
		return self.time

	def get_vid(self):
		return self.vid

	def play(self):
		self.status='loading'
		self.show_loading_screen()
		self.ready.acquire()
		if self.status=='invalid':
			return
		self.vlcPlay()
		self.status='finishing'

	def show_loading_screen(self):
		self.loading_screen=loading.LoadingScreen()
		self.loading_screen.show()

	def hide_loading_screen(self):
		self.loading_screen.close()

	def pause(self):
		if self.status == 'paused':
			return
		if self.status != 'playing':
			raise Exception("Video is not playing")
		self.vlc_mp.pause()
		self.status='paused'

	def stop(self):
		if self.status == 'stopped':
			return
		if self.status != 'playing' and self.status != 'paused':
			raise Exception("Video is not playing nor paused")
		self.vlc_mp.stop()
		self.status='stopped'

	def resume(self):
		if self.status == 'playing':
			return
		if self.status != 'paused':
			raise Exception("Video is not paused")
		self.vlc_mp.play()
		self.status='playing'

	def vlcPlay(self):
		os.environ["DISPLAY"] = ":0"
		self.vlc_i = vlc.Instance(['-f','--no-video-title-show'])
		self.vlc_mp = self.vlc_i.media_player_new()
		vlc_media=self.vlc_i.media_new_location(self.media)
		self.vlc_mp.set_media(vlc_media)
		self.vlc_mp.set_xwindow(0)
		self.vlc_mp.set_fullscreen(True)

		self.vlc_mp.play()

		# Loop continuously, getting output and setting titles
		while self.vlc_mp.get_state() not in [vlc.State.Ended,vlc.State.Stopped]:
			time.sleep(0.1)
			duration=self.vlc_mp.get_length()
			if duration>0:
				if self.status=='loading':
					self.hide_loading_screen()
					self.status='playing'
				self.duration=float(duration)/1000
				self.time=float(self.vlc_mp.get_time())/1000
		self.vlc_mp.stop()

	# Class variables

	commands={
		'pause':pause,
		'resume':resume,
		'stop':stop,
	}

	parameters={
		'url':get_url,
		'title':get_title,
		'duration':get_duration,
		'site':get_site,
		'media':get_media,
		'thumbnail':get_thumbnail,
		'description':get_description,
		'status':get_status,
		'time':get_time,
		'vid':get_vid,
	}

	# Low-level stuff.
	def getVideoInfo(self,url):
		# General configuration
		cookie_file='yt-cookies'
		jar = compat_cookiejar.MozillaCookieJar(cookie_file)
		if os.path.isfile(cookie_file) and os.access(cookie_file, os.R_OK):
			jar.load()
		cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
		proxies = compat_urllib_request.getproxies()
		proxy_handler = compat_urllib_request.ProxyHandler(proxies)
		https_handler = make_HTTPS_handler(None)
		opener = compat_urllib_request.build_opener(https_handler, proxy_handler, cookie_processor, YoutubeDLHandler())
		compat_urllib_request.install_opener(opener)
		socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

		y=youtube_dl.YoutubeDL({'outtmpl':'','format':'18'}) # empty outtmpl needed due to weird issue in youtube-dl
		y.add_default_info_extractors()

		try:
			info=y.extract_info(url,download=False)
		except Exception:
			self.status='invalid'
			self.queue.removeMeAsync(self.uid) # Remove if possible
			self.ready.release()
			return False

		vinfo=info['entries'][0]
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

		self.ready.release()
		return True

if __name__=='__main__':
	m=Youtube(None,None,"http://www.youtube.com/watch?v=F57P9C4SAW4")
	m.play()
