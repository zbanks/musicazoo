class YoutubeModule:
	TYPE_STRING="youtube"

	def __init__(self,url):
		self.url=url

	def getUrl(self):
		return url

	validCommands={
		'getUrl',getUrl
	}
