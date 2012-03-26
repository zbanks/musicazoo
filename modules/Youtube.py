from threading import Thread
from time import sleep
from subprocess import Popen, PIPE
import gdata.youtube.service as yt
import re

def getYouTubeIdFromUrl(url):
    try:
        return re.search(r"&v=(.*)$",url).group(1)
    except:
        #FIXME: I think this is funny. You may not.
        return "C_S5cXbXe-4" 

class Youtube:
    def __init__(self, json):
        self.json = json
        self.id = self.json["id"]
        self.url = self.json["url"]
        self.resources = ("audio", "screen")
        self.__gettitle()
        self.thread = None

    def run(self, cb):
        # Setup a thread to run the playyoutube command
        self.thread = Thread(target=self.__run, 
                             name="Youtube-%s"%self.id,
                             args=(cb,))
        self.thread.daemon = True
        self.thread.start();
            

    def pause(self, cb):
        self.kill()
        cb()

    def unpause(self, cb):
        self.run(cb)

    def kill(self):
        self.subprocess.kill()

    def status(self):
        output = {}
        output["id"] = self.id
        output["resources"] = self.resources
        output["title"] = self.title
        output["persistent"] = False # We do not want to be persistent
        return output
    
    def __gettitle(self):
        yt_service = yt.YouTubeService()
        entry = yt_service.GetYouTubeVideoEntry(video_id=getYouTubeIdFromUrl(self.url))
        self.title = entry.media.title.text        

    def __run(self,cb):
        # Compose the command and
        command = ["playyoutube", self.url]
        self.subprocess = Popen(command,stderr=PIPE, stdout=PIPE, stdin=PIPE)
        
        # Loop until the process has returned
        while self.subprocess.poll() == None:
            sleep(0.2)
            
        # We're done, let's call our callback and skidaddle
        cb()
        
        
        
