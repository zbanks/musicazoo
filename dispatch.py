import server
import re
import imp
import json
import threading
import os
import collections
import hashlib

# Address of dispatcher on network. (Address, Port)
ADDRESS = ('', 6785)
# Resources available to be used by queue items
RESOURCES = ("audio", "screen")
# Location of modules
MODULES_DIR = "/etc/musicazoo/modules/"

class Activity:
    def __init__(self,module,json):
        self.module = module
        self.id = hashlib.sha1(module+"".join(json)).hexdigest()
        self.resources = self.module.resources
        self.consumed = self.module.consumed
        self.persists = self.module.persists
        
    @classmethod
    def from_json(cls,json):
        try:
            module = Dispatch.modules(json["module"])
        except:
            print >> sys.stderr, "Module %s doesn't exist in local namespace!" % json["module"]
            #FIXME: Do something more sane
            raise
        return Activity(module,json)

    def start():
        #FIXME: make it actually start
        pass

class PlaybackState:
    def __init__(self, resources):
        self.state = dict(zip(resources,(True for n in len(resources)))))
        self.current_activities = dict(zip(resources,(None for n in len(resources))))) 
        
    def __getitem__(self, resource):
        return self.available(resource)

    def available(self,resource):
        return self.state.get(resource,False)

    def free(self, resource):
        if resource in self.state:
            if self.state[resource] == True:
                print >> sys.stderr, "Warning: freeing resource (%s) that is already free." % resource
            return self.state[resource] = True
        else:
            raise KeyError(resource)

    def use(self, resource):
        if resource in self.state:
            if self.state[resource] == False:
                print >> sys.stderr, "Warning! Resource %s already in use!" % resource
                #FIXME: Do something more sane
                raise Exception("Attempted to use resource that is already consumed")
            return self.state[resource] = False
        else:
            raise KeyError(resource)

    def idle(self, *resources):
        value = True
        for r in resources:
            value &= self.state[resources]
        return value

class PlaybackInterface:
    resources = RESOURCES[:]
    def __init__(self,queue=None,state=None):
        self.queue = queue or collections.deque()
        self.state = state or PlaybackState(PlaybackInterface.resources)
        
    def enque(self, json):
        try:
            activity = Activity.from_json(json)
        except:
            print >> sys.stderr, "Error tiestoenqueuing Activity from json '%s'." % json
            return
        
        queue.append(activity)
        if self.state.idle(activity.resources):
            self.start(activity)

    def start(self, activity):
        #FIXME: Do something
        pass
        
    

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
