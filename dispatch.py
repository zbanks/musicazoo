import server
import re
import imp
import json
import threading
import os
import collections
import hashlib
import time
import copy 
import sys

# Address of dispatcher on network. (Address, Port)
ADDRESS = ('', 6785)
# Resources available to be used by queue items
RESOURCES = ("audio", "screen")
# Location of modules
MODULES_DIR = "/etc/musicazoo/modules/"

"""
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
"""

def optional_list(f):
    def _f(_self, arg):
        if isinstance(arg, collections.Iterable) and not isinstance(arg, str):
            return f(_self, arg)
        else:
            return f(_self, [arg])
    return _f

class PlaybackState:
    def __init__(self, resources):
        self.state = dict(zip(resources, [True] * len(resources)))
        self.current_activities = dict(zip(resources, [None] * len(resources)))
        self.persistence = dict(zip(resources, [False] * len(resources)))
    def __getitem__(self, resource):
        return self.available(resource)

    @optional_list
    def available(self,resources):
        value = True
        for r in resources:
            value &= self.state.get(r, True)
        return value

    @optional_list
    def available_over_persistent(self,resources):
        value = True
        for r in resources:
            value &= self.state.get(r, True) or self.persistence.get(r, True)
        return value

    @optional_list
    def free(self, resources):
        for resource in resources:  
            if resource in self.state:
                if self.state[resource] == True:
                    print >> sys.stderr, "Warning: freeing resource (%s) that is already free." % resource
                self.state[resource] = True
                self.current_activities[resource] = None
                self.persistence[resource] = False
            else:
                raise KeyError(resource)
        return True

    @optional_list
    def use_over_persistent(self, resources, id="", persistence=False):
        pause_ids = []
        for resource in resources:
            if resource in self.state:
                if self.state[resource] == False and self.persistence[resource] == False:
                    print >> sys.stderr, "Warning! Resource %s already in use!" % resource
                    #FIXME: Do something more sane
                    raise Exception("Attempted to use resource that is already consumed")
                if self.state[resource]:
                    pause_ids.push(self.current_activies[resource])
                self.state[resource] = False
                self.persistence[resource] = persistence
                self.current_activities[resource] = id
            else:
                raise KeyError(resource)
        return pause_ids


    @optional_list
    def use(self, resources, id="", persistence=False):
        for resource in resources:
            if resource in self.state:
                if self.state[resource] == False:
                    print >> sys.stderr, "Warning! Resource %s already in use!" % resource
                    #FIXME: Do something more sane
                    raise Exception("Attempted to use resource that is already consumed")
                self.state[resource] = False
                self.persistence[resource] = persistence
                self.current_activities[resource] = id
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
        self.running = {} 

    def enque(self, activity):
        try:
            pass
#activity = Activity.from_json(json,)
        except:
            print >> sys.stderr, "Error enqueuing Activity from json '%s'." % json
            return
        
        self.queue.append(activity)
        self.refresh()
        
    def playing(self):
        return map(lambda act: act.status(), self.running)
    
    def refresh(self):
        if 0 == len(self.queue):
            return
        act = self.queue[0]
        status = act.status()
        if self.state.available(status["resources"]):
            self.state.use(status["resources"], status["id"], status["persistent"])
            self.queue.pop()
            self.run(act)
            self.refresh()
        elif self.state.available_over_persistent(status["resources"]):
            self.state.use_over_persistent(status["resources"], status["id"], status["persistent"]) 

    def run(self, activity):
        status = activity.status()
        def cb():
            print "Callback from run"
            self.running.pop(status["id"])
            self.state.free(status["resources"])
            self.refresh()

        if not self.state.available(status["resources"]):
            print >> sys.stderr, "Error running Activity, resources taken."
            return
        self.running[status["id"]] = activity
        activity.run(cb)
 
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
        print "Received data:", json_data
        if "module" in json_data:
            if json_data["module"] in self.modules:
                json_data["id"] = hashlib.sha1(json_data["module"]+str(time.time())+str(time.clock())).hexdigest()
                activity = self.modules[json_data["module"]](json_data)
                self.interface.enque(activity)
            else:
                print >> sys.stderr, "JSON tried to load module '%s' which does not exist" % json_data["module"]
        else:
            print >> sys.stderr, "JSON does not contain a 'module' field"

    def load_modules(self):
        for filename in os.listdir(MODULES_DIR):
            if filename.endswith(".py") and not filename.startswith("_"):
                filepath = os.path.join(MODULES_DIR, filename)
                name = filename[:-3] # Name of module, minus .py
                try:
                    module = imp.load_source(name, filepath)
                    if "modules" in dir(module):
                        for mname in module.modules:
                            if mname in dir(module):
                                Dispatch.modules[mname] = module.__dict__[mname]
                                print >> sys.stderr, "Imported module %s from %s" % (mname, filename)
                            else:
                                print >> sys.stderr, "No class named %s in module %s.py" % (mname, mname)
                    else:
                        if name in dir(module):
                            self.modules[name] = module.__dict__[name]
                            print >> sys.stderr, "Imported module %s from %s" % (name, filename)
                        else:
                            print >> sys.stderr, "No class named %s in module %s.py" % (name, name)
                except Exception, e:
                    print >> sys.stderr, "Error loading module %s: %s" % (name, e)

if __name__ == "__main__":
    dispatch = Dispatch()
    s = server.Server(ADDRESS, dispatch)
    s.serve_forever()
