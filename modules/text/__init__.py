import preprocessors
import text2speech
import renderers
import threading
import tempfile

class Text:
	TYPE_STRING='text'

	preprocessing_engines={
		'none':preprocessors.no_preprocessor,
		'pronounciation':preprocessors.pronounciation,
		'pronounce_email':preprocessors.pronounce_email,
		'pronounce_fortune':preprocessors.pronounce_fortune,
		'email':preprocessors.no_preprocessor, #TODO
		'remove_urls':preprocessors.remove_urls,
	}

	text2speech_engines={
		'none':text2speech.no_text2speech,
		'google':text2speech.google,
	}

	rendering_engines={
		'splash':renderers.Splash,
		'email':renderers.Email,
		'mono_paragraph':renderers.MonoParagraph,
	}

	def __init__(self,queue,uid,text,short_description=None,long_description=None,text_preprocessor='none',speech_preprocessor='pronounciation',text2speech='google',renderer='splash',duration=0,speed=1.0):
		self.queue=queue
		self.uid=uid

		self.text=text
		self.short_description=short_description
		if long_description is not None:
			self.long_description=long_description
		else:
			self.long_description=short_description
		self.speed=speed

		self.text_preprocessor=self.preprocessing_engines[text_preprocessor]
		self.speech_preprocessor=self.preprocessing_engines[speech_preprocessor]
		self.text2speech=self.text2speech_engines[text2speech]

		self.sndfile=tempfile.NamedTemporaryFile()

		self.renderer=self.rendering_engines[renderer]
		self.duration=duration

		self.ready=threading.Semaphore(0)

		self.status='added'

		t=threading.Thread(target=self.prepare)
		t.daemon=True
		t.start()

	def get_status(self):
		return self.status

	def get_text(self):
		return self.text

	def get_short_desc(self):
		return self.short_description

	def get_long_desc(self):
		return self.long_description

	def get_duration(self):
		if self.status!='ready':
			return None
		if self.status!='playing' and self.hasSound:
			return None
		return self.duration

	def prepare(self):
		try:
			self.textToShow=self.text_preprocessor(self.text)
			self.textToSpeak=self.speech_preprocessor(self.text)
			self.hasSound=self.text2speech(self)
			self.display=self.renderer(self)
			self.status='ready'
		except Exception:
			raise
			self.status='invalid'
			self.queue.removeMeAsync(self.uid)
		self.ready.release()

	def play(self):
		self.ready.acquire()
		if self.status != 'ready':
			return
		self.status='playing'
		self.display.play()
		self.status='finishing'
		self.sndfile.close()

	def stop(self):
		if self.status != 'playing':
			raise Exception("Not playing -- cannot stop")
		self.display.stop()
		self.status='stopped'

	commands={
		'stop':stop
	}

	parameters={
		'status':get_status,
		'text':get_text,
		'duration':get_duration,
		'short_description':get_short_desc,
		'long_description':get_long_desc,
	}
