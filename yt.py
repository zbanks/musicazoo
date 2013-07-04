class YoutubeModule:
	TYPE_STRING="youtube"

	def __init__(self,url):
		self.url=url

	def get_url(self):
		return self.url

	validCommands={
		'get_url':get_url
	}
