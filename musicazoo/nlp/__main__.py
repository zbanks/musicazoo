import json
import os
import random
import re
import signal
import socket
import subprocess
import tornado.httpclient
import traceback
import urllib
import urllib2

import shmooze.lib.packet as packet
import shmooze.lib.service as service
import shmooze.settings as settings

class NLP(service.JSONCommandProcessor, service.Service):
    port=settings.ports["nlp"]
    queue_host='localhost'
    queue_port=settings.ports["queue"]

    vol_host='localhost'
    vol_port=settings.ports["vol"]

    pretty_params={'youtube':['title'],  'text': ['text']}

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
                "help": "Play video from YouTube",
                "match": 0,
            })
        raise service.Return(results)

    @service.coroutine
    def url_suggest(self, url):
        #TODO
        results = [{
            "title": url,
            "action": url,
            "help": "",
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
        for sc, sc_help in self.suggest_commands:
            if sc.startswith(stripped_message):
                suggestions.append({
                    "title": sc,
                    "action": sc,
                    "help": sc_help,
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
        raise service.Return("Volume is {0}".format(result.get("vol", "unknown")))

    @service.coroutine
    def cmd_queue(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise service.Return("Queue is empty.")
        result = '\n'.join([u"{0}. {1}".format(n+1,self.pretty(mod)) for (n,mod) in enumerate(queue)])
        raise service.Return(result)

    @service.coroutine
    def cmd_current(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise service.Return("(Nothing)")
        result = self.pretty(queue[0])
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
        title = result[0]["title"]

        yield self.queue_cmd("add",{"type":"youtube","args":{"url":url}})

        raise service.Return(u'Queued "{0}"'.format(title))

    @service.coroutine
    def cmd_youtube_raw(self,q,url):
        yield self.queue_cmd("add",{"type":"youtube","args":{"url": url}})
        raise service.Return(u'Queued text.')

    @service.coroutine
    def cmd_image(self,q,url):
        yield self.queue_cmd("set_bg",{"type":"image","args":{"url": url}})
        raise service.Return(u'Queued text.')

    @service.coroutine
    def cmd_say(self,q,text):
        yield self.queue_cmd("add",{"type":"text","args":{"text":text}})
        raise service.Return(u'Queued text.')

    @service.coroutine
    def cmd_swear(self,q):
        # Swear words according to yahoo chat.
        # See: http://ridiculousfish.com/blog/posts/YahooChatRooms.html
        words = "ahole,aholes,asshole,assholes,asswipe,biatch,bitch,bitches,blo_job,blow_job,blowjob,cocksucker,cunt,cunts,dickhead,fuck,fucked,fucking,fuckoff,fucks,handjob,handjobs,motherfucker,mother-fucker,motherfuckers,muthafucker,muthafuckers,nigga,niggs,nigger,niggers,pedofile,pedophile,phag,phuc,phuck,phucked,phucker,shat,shit,shits,shithead,shitter,shitting".split(",") 
        selection = random.sample(words, 5)
        text = " ".join(selection)
        yield self.queue_cmd("add",{"type":"text","args":{"text":text}})
        raise service.Return(u'Queued swearing.')

    @service.coroutine
    def cmd_fortune(self, q):
        fortune_args = settings.get("fortune_args", ['-s'])
        fortune_text = subprocess.check_output(['/usr/games/fortune'] + fortune_args)
        data = {
            'type': 'text',
            'args': {
                'text': fortune_text,
                #'screen_preprocessor': 'none',
                'speech_preprocessor': 'pronounce_fortune',
                'text2speech': 'google',
                'text2screen': 'paragraph',
                #'renderer': 'mono_paragraph',
                'duration': 5,
            }
        }
        yield self.queue_cmd("add", data)
        raise service.Return(u"Queued fortune.")

    def pretty(self,mod):
        t=mod['type']
        if t=='youtube' and 'title' in mod['parameters']:
            return u'"{0}"'.format(mod['parameters']['title'])
        #if t=='netvid':
        #    return u'{0}'.format(mod['parameters']['short_description'])
        if t=='text' and 'text' in mod['parameters']:
            return u'"{0}"'.format(mod['parameters']['text'])
        return u'({0})'.format(t)

    @service.coroutine
    def cmd_bug(self,q,text):
        bug_url = "https://api.github.com/repos/zbanks/musicazoo/issues"
        suffix = "\n\nSubmitted via NLP service."
        bug_data = json.dumps({'title': text, 'body' : text + suffix})
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        try:
            password_mgr.add_password(None, bug_url, settings.github_login[0], settings.github_login[1])
        except AttributeError:
            raise service.Return(u"No github account configured in settings.json")

        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        #TODO request(bug_url, bug_data, auth=(musicazoo-bugs, musicaz00)
        raise service.Return(u'Submitted bug: %s - thanks!')

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
cur|current - Give the current item playing
bug - Submit a bug report
Anything else - Queue Youtube video""")

    commands={
        'do': do,
        'suggest': suggest,
    }

    suggest_commands = [
        ("vol up", "Raise the volume"),
        ("vol down", "Lower the volume"),
        ("skip", "Remove the current item on the queue that is currently playing"),
        ("pop", "Remove the last item on the queue"),
        ("bump", "Move the last item on the queue to top of the queue and play it"),
        ("say", "`say <quote>`: Say a quote and display it on the screen"),
        ("fuck", "Swear a bunch"),
        ("quote", "Display a quote from the fortune database"),
        ("image", "`image <url>`: Display an image on the screen as a background"),
        ("video", "`video <url>`: Play a video"),
    ]

    #TODO: splash
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
        (r'^fuck$',cmd_swear),
        (r'^fortune$',cmd_fortune),
        (r'^quote$',cmd_fortune),
        (r'^q$',cmd_queue),
        (r'^queue$',cmd_queue),
        (r'^cur(?:rent)?$',cmd_current),
        (r'^say (.+)$',cmd_say),
        (r'^image (.+)$',cmd_image),
        (r'^youtube (.+)$',cmd_youtube_raw),
        (r'^video (.+)$',cmd_youtube_raw),
        (r'^bug (.+)$',cmd_bug),
        (r'(https?://.+(?:gif|jpe?g|png|bmp))',cmd_image),
        (r'(https?://.+)',cmd_youtube_raw),
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
