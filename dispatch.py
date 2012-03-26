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

def optional_list(f):
    def _f(_self, arg, *args, **kwargs):
        if isinstance(arg, collections.Iterable) and not isinstance(arg, str):
            return f(_self, arg, *args, **kwargs)
        else:
            return f(_self, [arg], *args, **kwargs)
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
        self.queue_cmds = {"rm": self.rm_cmd,
                           "mv": self.mv_cmd }

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
            pause_ids = self.state.use_over_persistent(status["resources"], status["id"], status["persistent"]) 
            for id in pause_ids:
                if id in self.running:
                    try:
                        self.running[id].pause()
                    except:
                        print >> sys.stdrr, "Error pausing Activity"
                else:
                    print >> sys.stderr, "Attempted to pause activity which is not running."
            self.queue.pop()
            self.run(act)
            self.refresh()

    def run(self, activity):
        def cb():
            print "Callback from run"
            self.stop(activity, killed=True)
            self.refresh()

        status = activity.status()
        self.running[status["id"]] = activity
        try:
            activity.run(cb)
        except:
            print >> sys.stderr, "Error running activity"

    def stop(self, activity, killed=False):
        status = activity.status()
        if not killed:
            try:
                activity.kill()
            except:
                print >> sys.stderr, "Error killing activitiy"
        self.running.pop(status["id"])
        self.state.free(status["resources"])

    def send_message(self, for_id, json):
        if for_id in self.running:
            try:
                self.running[for_id].message(json)
            except:
                print >> sys.stderr, "Error sending message"
    
    def rm_cmd(self, json):
        if "all" in json and json["all"]:
            for act in self.running.values():
                self.stop(act)
        elif "id" in json and json["id"] in self.running:
            self.stop(self.running[json["id"]])
        self.refresh()

    def mv_cmd(self, json):
        #TODO: Move things around
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
        print "Received data:", json_data
        if "for_id" in json_data:
            for_id = json_data["for_id"]
            self.interface.send_message(for_id, json_data)
        elif "queue_cmd" in json_data:
            queue_cmd = json_data["queue_cmd"]
            if queue_cmd in self.interface.queue_cmds:
                self.interface.queue_cmds[queue_cmd](json_data)
        elif "module" in json_data:
            if json_data["module"] in self.modules:
                json_data["id"] = hashlib.sha1(json_data["module"]+str(time.time())+str(time.clock())).hexdigest()
                try:
                    activity = self.modules[json_data["module"]](json_data)
                except:
                    print >> sys.stderr, "Error initializing module %s" % json_data["module"]
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
