#import Youtube
from Video import Video
import gdata.youtube.service as yt

def getUrlFromKeyword(keyword):
     yt_service = yt.YouTubeService()
     query = yt.YouTubeVideoQuery()
     query.vq = keyword
     query.orderby = "relevance"
     feed = yt_service.YouTubeQuery(query)
     
     if len(feed.entry) != 0:
         return feed.entry[0].media.player.url.partition("&")[0]
     else:
         return ""

class YoutubeKeyword(Video):
    keywords = ("keyword",)
    catchall = True

    @staticmethod
    def match(input_str):
        return False

    def __init__(self, json):
        keyword = json["arg"]
        json["keyword"] = keyword

        # Get top related youtube video
        json["url"] = getUrlFromKeyword(keyword)
        self.url = json["url"]
        json["arg"] = json["url"]

        # Call superclass constructor
#return Youtube.Youtube.__init__(self,json)
#return super(YoutubeKeyword, self).__init__(json)
        return Video.__init__(self, json)

    def run(self, cb):
        if self.url != "":
            return Video.run(self, cb)
        else:
            cb()

