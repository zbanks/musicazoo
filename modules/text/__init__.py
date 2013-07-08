import preprocessors
import text2speech
import renderers
import threading

class Text:
	TYPE_STRING='text'

	preprocessing_engines={
		'none':preprocessors.no_preprocessor,
	}

	text2speech_engines={
		'none':text2speech.no_text2speech,
		'google':text2speech.google
	}

	rendering_engines={
		'splash':renderers.splash
	}

	def __init__(self,queue,uid,text,text_preprocessor='none',speech_preprocessor='none',text2speech='google',renderer='splash',duration=0):
		self.queue=queue
		self.uid=uid

		self.text=text
		self.text_preprocessor=self.preprocessing_engines[text_preprocessor]
		self.speech_preprocessor=self.preprocessing_engines[speech_preprocessor]
		self.text2speech=self.text2speech_engines[text2speech]
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

	def get_duration(self):
		return self.duration

	def prepare(self):
		try:
			self.textToShow=self.text_preprocessor(self.text)
			self.textToSpeak=self.speech_preprocessor(self.text)
			self.text2speech(self)
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
		self.renderer(self)

	commands={
	}

	parameters={
		'status':get_status,
		'text':get_text,
		'duration':get_duration,
	}
