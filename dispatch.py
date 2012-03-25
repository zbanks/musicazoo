import server
import re
import imp
import json
import threading
import os
import collections
import hashlib
import time

# Address of dispatcher on network. (Address, Port)
ADDRESS = ('', 6785)
# Resources available to be used by queue items
RESOURCES = ("audio", "screen")
# Location of modules
MODULES_DIR = "/etc/musicazoo/modules/"

class Activity:
    @classmethod
    def from_json(cls,json):
        try:
            module = Dispatch.modules(json["module"])
        except:
            print >> sys.stderr, "Module %s doesn't exist in local namespace!" % json["module"]
            #FIXME: Do something more sane
            raise
        return Activity(module,json)

    def __init__(self,module,json,callback):
        self.module = module
        self.instance = self.module.MusicazooLoader(json)
        self.id = hashlib.sha1(module+str(time.time())+str(time.clock())).hexdigest()
        self.resources = self.instance.resources
        self.persists = self.instance.persists

    def start(self):
        def kill_activity():
            return self.__kill()
        
        self.instance.start(kill_activity)

    def __kill(self):
        #FIXME: make it actually kill stuff
        pass
        
    def rm(self):
        self.instance.rm()

    def pause(self):
        self.instance.pause()


def optional_list(f):
    def _f(_self, arg):
        if isinstance(arg, collections.Iterables):
            return f(_self, arg)
        else:
            return f(_self, [arg])
    return _f

class PlaybackState:
    def __init__(self, resources):
        self.state = dict(zip(resources,(True for n in len(resources)))))
        self.current_activities = dict(zip(resources,(None for n in len(resources)))))
    def __getitem__(self, resource):
        return self.available(resource)

    @optional_list
    def available(self,resources):
        value = True
        for r in resources:
            value &= self.state.get(resource, True)
        return value

    @optional_list
    def free(self, resources):
        for resource in resources:  
            if resource in self.state:
                if self.state[resource] == True:
                    print >> sys.stderr, "Warning: freeing resource (%s) that is already free." % resource
                    return self.state[resource] = True
            else:
                raise KeyError(resource)
        return True

    @optional_list
    def use(self, resources):
        for resource in resources:
            if resource in self.state:
                if self.state[resource] == False:
                    print >> sys.stderr, "Warning! Resource %s already in use!" % resource
                    #FIXME: Do something more sane
                    raise Exception("Attempted to use resource that is already consumed")
                self.state[resource] = False
            else:
                raise KeyError(resource)
        return True
"""
    def resources_are_idle(self, resources):
        value = True
        for r in resources:
            value &= self.available(r)
        return value

    def remove(self, resources):
        for r in resources:
            self.free(r)
"""

class PlaybackInterface:
    resources = RESOURCES[:]
    def __init__(self,queue=None,state=None):
        self.queue = queue or collections.deque()
        self.state = state or PlaybackState(PlaybackInterface.resources)
        
    def enque(self, json):
        try:
            activity = Activity.from_json(json,)
        except:
            print >> sys.stderr, "Error enqueuing Activity from json '%s'." % json
            return
        
        queue.append(activity)
        
   
class Dispatch:
    """
    Dispatch

    Reads in JSON objects over socket and dispatches commands,
    manages queue, and switches between program modules.
    """
    modules = {}
    def __init__(self,interface=None):
        self.load_modules()
        self.interface = interface or PlaybackInterface()

    def from_data(self, json_data):
        #FIXME: Makde this add things to the queue
        print json_data

    def load_modules(self):
        for filename in os.listdir(MODULES_DIR):
            if filename.endswith(".py") and not filenames.startswith("_"):
                filepath = os.path.join(MODULES_DIR, filenames)
                name = filename[:-3] # Name of module, minus .py
                try:
                    module = imp.load_source(name, filepath)
                except Exception, e:
                    print >> sys.stderr, "Error loading module %s: %s" % (name, e)
                else:
                    Dispatch.modules["name"] = module


if __name__ == "__main__":
    dispatch = Dispatch()
    s = server.Server(ADDRESS, dispatch)
    s.serve_forever()
