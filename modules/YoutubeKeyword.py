import Youtube
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

class YoutubeKeyword(Youtube.Youtube):
    def __init__(self, json):
        keyword = json["keyword"]
        
        # Get top related youtube video
        json["url"] = getUrlFromKeyword(keyword)

        # Call superclass constructor
        Youtube.Youtube.__init__(self,json)


    def run(self, cb)        
        if self.url != "":
            Youtube.Youtube.run(self,cb)
        else:
            cb()


    def kill(self, cb):
        if self.url != "":
            Youtube.Youtube.kill()
        
        
