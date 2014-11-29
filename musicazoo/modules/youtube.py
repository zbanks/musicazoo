import os
import tempfile
import threading
import time
import youtube_dl

from youtube_dl.compat import compat_cookiejar, compat_urllib_request
from youtube_dl.utils import make_HTTPS_handler, YoutubeDLHandler
from musicazoo.lib.vlc_player_compat import Player
from musicazoo.lib.loading import LoadingScreen

from musicazoo.lib.watch_dl import WatchCartoonOnlineIE

class Youtube:
	TYPE_STRING='youtube'

	def __init__(self,queue,uid,url):
		self.player=Player()
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
		self.rate=None
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
		if self.status=='invalid' or self.status=='stopped':
			self.hide_loading_screen()
			return
		self.vidPlay()
		self.status='finishing'

	def show_loading_screen(self):
		self.loading_screen=LoadingScreen()
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

		if self.status=='loading' or self.status=='added':
			self.hide_loading_screen()

		if self.player.up():
			self.player.stop()
		self.status='stopped'
		self.ready.release()

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
			t=self.player.time()
			if t is not None:
				if self.status=='loading':
					self.hide_loading_screen()
					self.status='playing'
				self.time=t
				self.duration=self.player.length()
				self.rate=self.player.get_rate()


		if self.status=='loading':
			self.hide_loading_screen()

		self.rate=None
		self.player.stop()

		if self.cookies:
			os.unlink(self.cookies)

	def set_rate(self,rate):
		if not self.player.up():
			raise Exception("Cannot set rate of video that is not playing")
		self.player.set_rate(rate)

	def get_rate(self):
		return self.rate

	def seek_rel(self,offset):
		if not self.player.up():
			raise Exception("Video is not up")
		self.player.seek_rel(offset)

	def seek_abs(self,position):
		if not self.player.up():
			raise Exception("Video is not up")
		self.player.seek_abs(position)

	# Class variables

	commands={
		'pause':pause,
		'resume':resume,
		'stop':stop,
		'set_rate':set_rate,
		'seek_rel':seek_rel,
		'seek_abs':seek_abs,
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
		opener = compat_urllib_request.build_opener(https_handler, proxy_handler, cookie_processor, YoutubeDLHandler)
		compat_urllib_request.install_opener(opener)

		y=youtube_dl.YoutubeDL({'outtmpl':u'','skip_download':True, 'format_limit': 18}) # empty outtmpl needed due to weird issue in youtube-dl
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

		self.ready.release()
		return True

if __name__=='__main__':
	m=Youtube(None,None,"http://www.youtube.com/watch?v=F57P9C4SAW4")
	m.play()
