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
import subprocess

# Address of dispatcher on network. (Address, Port)
ADDRESS = ('', int(open("/tmp/portnum").readline().strip()))
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
                if not self.state[resource]:
                    print self.current_activities, "CURRR"
                    pause_ids.append(self.current_activities[resource])
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
                           "mv": self.mv_cmd,
                           "status": self.status_cmd }

    def enque(self, activity):
        self.queue.append(activity)
        self.refresh()
        return True
        
    def playing(self):
        output = []
        for act in self.running.values():
            try:
                output.append(act.status())
            except Exception as err:
                print >> sys.stderr, err
        return output
#return map(lambda act: act.status(), self.running.values())

    def queued(self):
        output = []
        for act in self.queue:
            try:
                output.append(act.status())
            except Exception as err:
                print >> sys.stderr, err
        return output
#return map(lambda act: act.status(), self.queue)
    
    def refresh(self):
        if 0 == len(self.queue):
            return
        act = self.queue[0]
        try:
            status = act.status()
        except Exception as err:
            print >> sys.stderr, err
            return False
        print "***", status, self.state.state, self.state.persistence, self.state.available(status["resources"]), self.state.available_over_persistent(status["resources"])
        if self.state.available(status["resources"]):
            self.state.use(status["resources"], status["id"], status["persistent"])
            self.queue.remove(act)
            self.run(act)
            self.refresh()
        elif self.state.available_over_persistent(status["resources"]):
            print status
            pause_ids = self.state.use_over_persistent(status["resources"], status["id"], status["persistent"]) 
            print pause_ids
            print self.playing()
            have_paused = dict([(i, False) for i in pause_ids])

            def _cb(pid):
                def cb():
                    have_paused[pid] = True
                    if all(have_paused.values()):
                        self.queue.remove(act)
                        self.run(act)
                        self.refresh() 
                return cb

            for id in pause_ids:
                if id in self.running:
                    try:
                        to_pause = self.running.pop(id)
                        self.queue.appendleft(to_pause)
                        to_pause.pause(_cb(id))
                    except Exception as err:
                        print >> sys.stderr, "Error pausing Activity"
                        print >> sys.stderr, err.message
                        self.stop(self.running[id])
                else:
                    print >> sys.stderr, "Attempted to pause activity which is not running."

    def run(self, activity):
        def cb():
            print "Callback from run"
            self.stop(activity, killed=True)
            self.refresh()

        def unpause_cb():
            print "Callback from run"
            self.refresh()

        try:
            status = activity.status()
            self.running[status["id"]] = activity
            if "screen" in status["resources"]:
                monitor_on()
            if status["running"]:
                activity.unpause(unpause_cb)
            else:
                activity.run(cb)
        except Exception as err:
            print >> sys.stderr, "Error running activity"
            print >> sys.stderr, err.message
            self.stop(activity)

    def stop(self, activity, killed=False):
        try:
            status = activity.status()
            if not "id" in status:
                raise Exception("No id")
        except Exception as err:
            print >> sys.stderr, "Error getting status from activity"
            print >> sys.stderr, err

        if not killed:
            try:
                activity.kill()
            except Exception as err:
                print >> sys.stderr, "Error killing activitiy"
                print >> sys.stderr, err.message
        print status["id"]
        print self.running.keys()
        if status["id"] in self.running:
            self.running.pop(status["id"])
            self.state.free(status["resources"])
        else:
            try:
                self.queue.remove(activity)
            except ValueError as err:
                print >> sys.stderr, "Activity not in queue or running"
                print >> sys.stderr, err.message


    def send_message(self, for_id, json):
        if for_id in self.running:
            try:
                self.running[for_id].message(json)
            except Exception as err:
                print >> sys.stderr, "Error sending message"
                print >> sys.stderr, err.message
    
    def rm_cmd(self, json):
        if "all" in json and json["all"]:
            for act in self.running.values():
                self.stop(act)
            for act in self.queue:
                self.stop(act)
        elif "id" in json: 
            if json["id"] in self.running:
                self.stop(self.running[json["id"]])
            #else:
#qus = list(self.queue)
            for act in self.queue:
                # Gahh, so inefficient :-(
                try:
                    if act.status()["id"] == json["id"]:
                        self.stop(act)
                        break
                except Exception, err:
                    print >> sys.stderr, "Error getting status"
                    print >> sys.stderr, err
        self.refresh()
        return {"success": True, "error": ""}

    def mv_cmd(self, json):
        #TODO: Move things around
        return {"success": False, "error": "Not implemented"}

    def status_cmd(self, json):
        return {"success": True, "error": "", "playing": self.playing(), "queue": self.queued()}  

    def reload_cmd(self, json):
        print "Reload"
        try:
            load_modules()
            return {"success": True, "error": ""}
        except:
            return {"success": False, "error": "Unable to reload modules"}
 
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
        print "Received data:", json_data
        if "for_id" in json_data:
            for_id = json_data["for_id"]
            output = self.interface.send_message(for_id, json_data)
            if output:
                return {"success": True, "error": ""}
            else:
                return {"success": False, "error": "Unable to send message"}
        elif "queue_cmd" in json_data:
            queue_cmd = json_data["queue_cmd"]
            if queue_cmd in self.interface.queue_cmds:
                output = self.interface.queue_cmds[queue_cmd](json_data)
                return output
            if queue_cmd == "reload":
                self.load_modules()
                return {"success": True, "error": ""}
        elif "module" in json_data:
            json_data["module"] = json_data["module"].lower()
            if json_data["module"] in self.modules:
                json_data["id"] = hashlib.sha1(json_data["module"]+str(time.time())+str(time.clock())).hexdigest()
                try:
                    activity = self.modules[json_data["module"]](json_data)
                except Exception as err:
                    print >> sys.stderr, "Error initializing module %s" % json_data["module"]
                    print >> sys.stderr, err.message
                else:
                    output = self.interface.enque(activity)
                    if output:
                        return {"success": True, "error": ""}
                    else:
                        return {"success": False, "error": "Unable to queue activitiy"}
            else:
                print >> sys.stderr, "JSON tried to load module '%s' which does not exist" % json_data["module"]
                return {"success": False, "error": "Unable to load module"}
        else:
            print >> sys.stderr, "JSON does not contain a 'module' field"
            return {"success": False, "error": "Malformed json, no module specified"}

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
                                self.modules[mname.lower()] = module.__dict__[mname]
                                print >> sys.stderr, "Imported module %s from %s" % (mname.lower(), filename)
                            else:
                                print >> sys.stderr, "No class named %s in module %s.py" % (mname, mname)
                    else:
                        if name in dir(module):
                            self.modules[name.lower()] = module.__dict__[name]
                            print >> sys.stderr, "Imported module %s from %s" % (name.lower(), filename)
                        else:
                            print >> sys.stderr, "No class named %s in module %s.py" % (name, name)
                except Exception, e:
                    print >> sys.stderr, "Error loading module %s: %s" % (name, e)
                    print >> sys.stderr, e.message()

def monitor_on():
    subprocess.Popen(("/etc/musicazoo/bin/monitor-on",))

def monitor_off():
    subprocess.Popen(("/etc/musicazoo/bin/monitor-off",))

if __name__ == "__main__":
    dispatch = Dispatch()
    s = server.Server(ADDRESS, dispatch)
    s.serve_forever()
