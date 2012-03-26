from threading import Thread
from time import sleep
from subprocess import Popen, PIPE

class Youtube:
    def __init__(self, json):
        self.json = json
        self.id = self.json["id"]
        self.url = self.json["url"]
        self.resources = ("audio", "screen")
        self.title = "Youtube Video: %s" % self.url
        self.thread = None
        # Now launch a thread to get the correct title!
        gettitle = Thread(target=self.__gettitle)
        gettitle.daemon = True
        gettitle.start()
        
    def run(self, cb):
        # Setup a thread to run the playyoutube command
        self.thread = Thread(target=self.__run, 
                             name="Youtube-%s"%self.id,
                             args=(cb,))
        self.thread.daemon = True
        self.thread.start();
            

    def pause(self, cb):
        self.kill()

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
        #FIXME: Lookup video title
        pass
        

    def __run(self,cb):
        # Compose the command and
        command = ["playyoutube", '"%s"' % self.url]
        self.subprocess = Popen(command,stderr=PIPE, stdout=PIPE, stdin=PIPE)
        
        # Loop until the process has returned
        while self.subprocess.returncode == None:
            sleep(0.2)
            self.subprocess.poll()
            
        # We're done, let's call our callback and skidaddle
        cb()
        
        
        
