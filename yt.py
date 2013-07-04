import time

class YoutubeModule:
	TYPE_STRING="youtube"

	def __init__(self,url):
		self.url=url

	def get_url(self):
		return self.url

	def play(self):
		print "PLAYING "+self.url
		time.sleep(10)
		print "DONE"

	validCommands={
		'get_url':get_url
	}
