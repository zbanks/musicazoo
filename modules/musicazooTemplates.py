from threading import Thread
from time import sleep
from subprocess import Popen, PIPE
import gdata.youtube.service as yt
import re

class MusicazooShellCommandModule:
    resources = ()
    persistent = False
    keywords = ()
    command = ()
    title = 'Musicazoo Module'
    
    def match(input_str):
        return False

    def __init__(self, json):
        # Make sure we don't allow people to run arbitrary commands via input
        if self.command == ():
            raise Exception("All shell command modules must define a command to run")

        self.__initialize(json)
        self.arg = json["arg"]
        self.command += (self.arg,)

    def __initialize(self, json):
        self.json = json
        self.id = json["id"]
        self.thread = None

    def run(self, cb):
        # Setup a thread to run the shell command
        self.thread = Thread(target=self.__run, 
                             name="Musicazoo-%s"%self.id,
                             args=(cb,))
        self.thread.daemon = True
        self.thread.start();
            

    def pause(self, cb):
        self.kill()
        cb()

    def unpause(self, cb):
        self.run(cb)

    def kill(self):
        if self.subprocess: self.subprocess.kill()

    def status(self):
        output = {}
        output["id"] = self.id
        output["resources"] = self.resources
        output["title"] = self.title
        output["persistent"] = self.persistent  # We do not want to be persistent
        return output
    
    def __run(self,cb):
        # Compose the command and
        command = self.command
        self.subprocess = Popen(command,stderr=PIPE, stdout=PIPE, stdin=PIPE)
        
        # Loop until the process has returned
        while self.subprocess.poll() == None:
            sleep(0.2)
            
        # We're done, let's call our callback and skidaddle
        cb()
        
        
        
