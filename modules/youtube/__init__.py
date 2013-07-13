import time

import youtube_dl
from youtube_dl.utils import *
import mplayer_player_compat as player
import threading
import os
import loading
import tempfile

class Youtube:
	TYPE_STRING='youtube'

	def __init__(self,queue,uid,url):
		self.player=player.Player()
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
		self.cookies=None
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
		self.show_loading_screen()
		self.ready.acquire()
		if self.status=='invalid':
			return
		self.vidPlay()
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
		self.player.pause()
		self.status='paused'

	def stop(self):
		if self.status == 'stopped':
			return
		if not self.player.up():
			raise Exception("Video is not up")
		self.player.stop()
		self.status='stopped'

	def resume(self):
		if self.status == 'playing':
			return
		if self.status != 'paused':
			raise Exception("Video is not paused")
		self.player.play()
		self.status='playing'

	def vidPlay(self):
		self.player.load(self.media,cookies=self.cookies)

		self.status='loading'

		# Loop continuously, getting output and setting titles
		while self.player.up():
			time.sleep(0.1)
			duration=self.player.length()
			if duration is not None:
				if self.status=='loading':
					self.hide_loading_screen()
					self.status='playing'
				self.duration=duration
				self.time=self.player.time()
		self.player.stop()
		if self.cookies:
			os.unlink(self.cookies)

	def set_rate(self,rate):
		if not self.player.up():
			raise Exception("Cannot set rate of video that is not playing")
		self.player.set_rate(rate)

	def get_rate(self):
		if not self.player.up():
			return None
		return self.player.get_rate()

	# Class variables

	commands={
		'pause':pause,
		'resume':resume,
		'stop':stop,
		'set_rate':set_rate,
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
		'rate':get_rate,
	}

	# Low-level stuff.
	def getVideoInfo(self,url):
		# General configuration
		tf=tempfile.NamedTemporaryFile(delete=False)
		tf.close()
		self.cookies=tf.name
		jar = compat_cookiejar.MozillaCookieJar(self.cookies)
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

		jar.save()

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
