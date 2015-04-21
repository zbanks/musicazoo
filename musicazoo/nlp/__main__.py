import shmooze.lib.service as service
import os
import signal
import traceback
import socket
import re
import shmooze.lib.packet as packet
import tornado.httpclient
import urllib
import json
import shmooze.settings as settings

class NLP(service.JSONCommandProcessor, service.Service):
    port=settings.ports["nlp"]
    queue_host='localhost'
    queue_port=settings.ports["queue"]

    vol_host='localhost'
    vol_port=settings.ports["vol"]

    pretty_params={'youtube':['title']}

    youtube_api_key = settings.youtube_api_key

    def __init__(self):
        print "NLP started."
        self.youtube_cache = {}
        super(NLP, self).__init__()

    @staticmethod
    def parse_duration(dstr):
        # Parse ISO 8601 duration strings: PT#M#S
        hms_str = dstr.strip()
        try:
            matches = re.match(r"PT(\d+H)?(\d{1,2}M)?(\d{1,2}S)", hms_str).groups()
        except:
            print hms_str
            return 0, hms_str
        h, m, s = [int(m.strip("HMS")) if m is not None else 0 for m in matches]

        if h > 0:
            human_str = "{0}:{1:02d}:{2:02d}".format(h, m, s)
        else:
            human_str = "{1}:{2:02d}".format(h, m, s)

        return h * 360 + m * 60 + s, human_str

    @service.coroutine
    def youtube_search(self,q):
        if q in self.youtube_cache:
            print "cache hit"
            raise service.Return(self.youtube_cache[q])
        print "cache miss"

        http_client = tornado.httpclient.AsyncHTTPClient()
        # Return the args dict for the first youtube result for 'match'
        youtube_search_url = "https://www.googleapis.com/youtube/v3/search"
        search_data = {
            "part": "snippet",
            "key": self.youtube_api_key,
            "order": "relevance",
            "safesearch": "none",
            "type": "video",
            "max-results": 5,
            "q": q,
        }
        search_form_data=urllib.urlencode(search_data)
        
        search_results = yield http_client.fetch(youtube_search_url+"?"+search_form_data)
        search_json = json.loads(search_results.body)

        video_ids = [v["id"]["videoId"] for v in search_json["items"]]

        youtube_video_url = "https://www.googleapis.com/youtube/v3/videos"
        video_data = {
            "part": "contentDetails,snippet,statistics",
            "key": self.youtube_api_key,
            "id": ",".join(video_ids),
        }
        video_form_data = urllib.urlencode(video_data)
        video_results = yield http_client.fetch(youtube_video_url + "?" + video_form_data)
        video_json = json.loads(video_results.body)

        output = []
        for yi in video_json['items']:
            sr = {
                "video_id": yi["id"], 
                "url": "http://www.youtube.com/watch?v={0}".format(yi["id"]), 
                "title": yi["snippet"]["title"], 
                "thumbnail": yi["snippet"]["thumbnails"]["default"]["url"], 
                "publish_time": yi["snippet"]["publishedAt"], 
                "views": yi["statistics"]["viewCount"], 
                "duration": self.parse_duration(yi["contentDetails"]["duration"]),
            }
            output.append(sr)

        self.youtube_cache[q] = output
        raise service.Return(output)

    @service.coroutine
    def youtube_suggest(self, q):
        videos = yield self.youtube_search(q)
        results = []
        for v in videos:
            results.append({
                "title": u"{0[title]} - [{0[duration][1]}]".format(v),
                "action": v["url"],
                "match": 0,
            })
        raise service.Return(results)

    @service.coroutine
    def url_suggest(self, url):
        #TODO
        results = [{
            "title": url,
            "action": url,
            "match": len(url)
        }]
        yield service.Return(results)

    @service.coroutine
    def wildcard_suggest(self, text):
        text = text.strip()
        results = []
        if text.startswith("http:"):
            rs = yield self.url_suggest(text)
            results.extend(rs)
        yr = yield self.youtube_suggest(text)
        results.extend(yr)
        raise service.Return(results)

    @service.coroutine
    def suggest(self,message):
        stripped_message = message.strip()
        suggestions = []
        for sc in self.suggest_commands:
            if sc.startswith(stripped_message):
                suggestions.append({
                    "title": sc,
                    "action": sc,
                    "match": len(stripped_message)
                })
        rs = yield self.wildcard_suggest(message)
        suggestions.extend(rs)
        raise service.Return({'suggestions':suggestions})

    @service.coroutine
    def queue_cmd(self,cmd,args={},assert_success=True):
        try:
            result = yield service.json_query(self.queue_host,self.queue_port,{"cmd":cmd,"args":args})
        except (socket.error,service.TimeoutError):
            raise Exception("Error communicating with queue.")
        if assert_success:
            raise service.Return(packet.assert_success(result))
        raise service.Return(result)

    @service.coroutine
    def vol_cmd(self,cmd,args={},assert_success=True):
        try:
            result = yield service.json_query(self.vol_host,self.vol_port,{"cmd":cmd,"args":args})
        except (socket.error,service.TimeoutError):
            raise Exception("Error communicating with volume control.")
        if assert_success:
            raise service.Return(packet.assert_success(result))
        raise service.Return(result)

    @service.coroutine
    def do(self,message):
        message=message.strip()
        for (regex,func) in self.nlp_commands:
            m=re.match(regex,message,re.I)
            if m:
                result = yield func(self,message,*m.groups())
                raise service.Return(result)
        raise Exception("Command not recognized.")

    #result = yield self.queue_cmd("queue")
        raise service.Return({'message':'Did '+message})

    def shutdown(self):
        service.ioloop.stop()

    @service.coroutine
    def cmd_set_vol(self,q,vol):
        if vol=='up':
            result=yield self.vol_cmd("get_vol")
            vol=min(result['vol']+5,100)
        elif vol=='down':
            result=yield self.vol_cmd("get_vol")
            vol=max(result['vol']-5,0)
        else:
            vol=int(vol)

        if vol>100:
            raise Exception("Volume cannot be greater than 100")
        yield self.vol_cmd("set_vol",{"vol":vol})

        raise service.Return("Volume set to {0}".format(vol))

    @service.coroutine
    def cmd_get_vol(self,q):
        result=yield self.vol_cmd("get_vol")
        raise service.Return("Volume is {0}".format(result))

    @service.coroutine
    def cmd_queue(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise Exception("Queue is empty!")
        result = '\n'.join([u"{0}. {1}".format(n+1,self.pretty(mod)) for (n,mod) in zip(range(len(queue)),queue)])
        raise service.Return(result)

    @service.coroutine
    def cmd_rm_top(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise Exception("Queue is empty!")
        mod=queue[0]
        yield self.queue_cmd("rm",{"uids":[mod['uid']]})
        raise service.Return(u"Removed {0}".format(self.pretty(mod)))

    @service.coroutine
    def cmd_rm_bot(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise Exception("Queue is empty!")
        mod=queue[-1]
        yield self.queue_cmd("rm",{"uids":[mod['uid']]})
        raise service.Return(u"Removed {0}".format(self.pretty(mod)))

    @service.coroutine
    def cmd_bump(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise Exception("Queue is empty!")
        if len(queue)==1:
            raise Exception("Only one thing on the queue!")
        old_uids=[mod['uid'] for mod in queue]
        mod_bot=queue[-1]
        new_uids=old_uids[-1:]+old_uids[0:-1]
        yield self.queue_cmd("mv",{"uids":[mod['uid']]})
        raise service.Return(u"Bumped {0} to the top".format(self.pretty(mod_bot)))

    @service.coroutine
    def cmd_yt(self,q,kw):
        result=yield self.youtube_search(kw)

        if not result or not result[0]:
            raise Exception('No Youtube results found.')

        url = result[0]["url"]

        yield self.queue_cmd("add",{"type":"youtube","args":{"url":url}})

        raise service.Return(u'Queued "{0}"'.format(title))

    @service.coroutine
    def cmd_say(self,q,text):
        yield self.queue_cmd("add",{"type":"text","args":{"text":text}})
        raise service.Return(u'Queued text.')

    def pretty(self,mod):
        t=mod['type']
        if t=='youtube' and 'title' in mod['parameters']:
            return u'"{0}"'.format(mod['parameters']['title'])
        #if t=='netvid':
        #    return u'{0}'.format(mod['parameters']['short_description'])
        #if t=='text':
        #    return u'{0}'.format(mod['parameters']['short_description'])
        return u'({0})'.format(t)

    @service.coroutine
    def cmd_help(self,q):
        raise service.Return("""Commands I understand:
help|? - This
vol - Get volume
vol [num] - Set volume
vol up|down - Change volume
stop|stfu|skip|next - Remove the top video
pop|undo|oops - Remove the bottom video
bump - Move the bottom video to the top
q|queue - List the queue
Anything else - Queue Youtube video""")

    commands={
        'do': do,
        'suggest': suggest,
    }

    suggest_commands = [
        "vol up",
        "vol down",
        "skip",
        "pop",
        "bump",
        "say",
    ]

    nlp_commands=[
        (r'^help$',cmd_help),
        (r'^$',cmd_help),
        (r'^\?$',cmd_help),
        (r'^vol (\d+|up|down)$',cmd_set_vol),
        (r'^vol$',cmd_get_vol),
        (r'^stop$',cmd_rm_top),
        (r'^stfu$',cmd_rm_top),
        (r'^skip$',cmd_rm_top),
        (r'^next$',cmd_rm_top),
        (r'^pop$',cmd_rm_bot),
        (r'^undo$',cmd_rm_bot),
        (r'^oops$',cmd_rm_bot),
        (r'^bump$',cmd_bump),
        (r'^q$',cmd_queue),
        (r'^queue$',cmd_queue),
        (r'^say (.+)$',cmd_say),
        (r'^(.+)$',cmd_yt),
    ]

nlp = NLP()

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(nlp.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
