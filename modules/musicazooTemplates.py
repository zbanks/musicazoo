from threading import Thread
from time import sleep
from subprocess import Popen, PIPE
import gdata.youtube.service as yt
import re
import os

null_f = open("/dev/null", "rw")

class MusicazooShellCommandModule(object):
    resources = ()
    persistent = False
    keywords = ()
    catchall = False 
    command = ()
    title = '(Module)'
    status_dict = {}
    queue_html = None
    playing_html = None
    subprocess = None
    running = False
    
    @staticmethod
    def match(input_str):
        return False

    def __init__(self, json):
        # Make sure we don't allow people to run arbitrary commands via input
        if self.command == ():
            raise Exception("All shell command modules must define a command to run")

        self.status_dict = {} #possibly causing issues? 
        self._initialize(json)
        self.arg = json["arg"]
        self.command += (self.arg,)
        self.title = "(%s)" % self.__class__.__name__

    def _initialize(self, json):
        self.json = json
        self.id = json["id"]
        self.thread = None

    def run(self, cb):
        # Setup a thread to run the shell command
#command = self.command
#self.subprocess = Popen(command, shell=False, stderr=null_f, stdout=null_f, stdin=PIPE)
        self.running = True
        self.thread = Thread(target=self._run, 
                             name="Musicazoo-%s"%self.id,
                             args=(cb,))
        self.thread.daemon = True
        self.thread.start();
            


    def pause(self, cb):
        self.kill()
        self.running = True
        cb()

    def unpause(self, cb):
        self.run(cb)

    def kill(self):
        if self.subprocess:
            os.system("killtree %d" % self.subprocess.pid)
        self.running = False

    def status(self):
        output = self.status_dict
        output["running"] = self.running
        output["id"] = self.id
        output["resources"] = self.resources
        output["persistent"] = self.persistent  # We do not want to be persistent
        output["title"] = self.title
        output["queue_html"] = self.queue_html
        output["playing_html"] = self.playing_html

        if not self.queue_html:
            output["queue_html"] = self.title
        if not self.playing_html:
            output["playing_html"] = self.title
        return output
    
    def message(self,json):
        pass

    def _run(self,cb):
        # Compose the command and start the subprocess
        command = self.command
        self.subprocess = Popen(command,stderr=null_f, stdout=null_f, stdin=PIPE)
        
        # Loop until the process has returned
        while self.subprocess.poll() == None:
            sleep(0.2)
#self.subprocess.wait()
            
        # We're done, let's call our callback and skidaddle
        cb()
        
        
        
