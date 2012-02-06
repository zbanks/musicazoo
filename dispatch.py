import server
import re
import imp
import json
import threading
import os

# Address of dispatcher on network. (Address, Port)
ADDRESS = ('', 6785)
# Resources available to be used by queue items
RESOURCES = set(["audio", "screen"])
# Location of modules
MODULES_DIR = "/etc/musicazoo/modules/"

class Queue:
    def __init__(self):
        # Queue containing JSON objects to be played (blocking)
        self.queue = []
        # Queue containing JSON objects that can be played instantly
        self.instant = []
        # Set of persistent items. {"audio": None, "screen": None }
        self.persist = [] #dict(zip(RESOURCES, [None for i in RESOURCES]))
        # Source of currently playing items
        self.playing_from_queue = True
        
        # ID assigned to next item on queue
        self.next_id = 0 

        # Items that need to be started/ended
        self.started = []
        self.ended = []

    def current(self):
        """
        Return a list of items currently playing
        """
        playing = []
        if self.playing_from_queue:
            playing.append(self.queue[0])
            queue_resources = set(self.queue[0]["resources"])
            open_resources = RESOURCES.difference(queue_resources)
            for persist_item in self.persist:
                if persist_item["resources"].issubset(open_resources):
                    playing.append(persist_item)
                    open_resources = open_resources.difference(persist_item["resources"]) 
        else:
            playing += self.persist
        playing += self.instant
        return playing
    
    def rm(self, qid):
        f = lambda xs: filter(lambda x: x["id"] != qid, xs)
        self.queue = f(self.queue)
        self.instant = f(self.instant)
        self.persist = f(self.persist)

    def push(self, jsonitem):
        jsonitem["id"] = self.next_id
        self.next_id += 1
        if jsonitem["instant"]:
            self.instant.append(jsonitem)
        elif jsonitem["persist"]:
            new_persist = [jsonitem]
            popped = []
            for pitem in self.persist:
                if set(pitem["resources"]).intersect(set(jsonitem["resources"])) != set([]):
                    popped.append(pitem)
                else:
                    new_persist.append(pitem)
            self.persist = new_persist
        else:
             self.queue.append(jsonitem)
        return jsonitem

class Dispatch:
    """
    Dispatch

    Reads in JSON objects over socket and dispatches commands,
    manages queue, and switches between program modules.
    """
    def __init__(self):
        self.queue = Queue()
        self.current = []
        self.modules = {}
        self.load_modules()

    def from_data(self, json):
        """
        Recieve & Parse JSON data
        """ 
        def error(desc):
            return "{'error': '%s'}" % desc.replace("'", '"')
        
        if json["cmd"] == "item":
            output = self.cmd_item(json)
        elif json["cmd"] == "queue":
            output = self.cmd_queue(json)
        return json.dumps(output)

    def cmd_item(self, json):
        def error(desc):
            return "{'error': '%s'}" % desc

        module_name = json["module"]
        if module_name in self.modules:
            module = self.modules[module_name]
        else:
            return error("Unable to find module %s" % module_name)
        
        try:
            queue_obj = module.MusicazooLoader(json)
            # Append to queue
            self.queue.push(json)
            return {"error": None }
        except:
            return error("Error loading module %s" % module_name)

    def cmd_queue(self, json):
        return {"queue": self.queue.queue,
                "current": self.queue.current() }

    def load_modules(self):
        """
        Load plugin modules
        """
        for filename in os.listdir(MODULES_DIR):
            if filename.endswith(".py") and not filenames.startswith("_"):
                filepath = os.path.join(MODULES_DIR, filenames)
                name = filename[:-3] # Name of module, minus .py
                try:
                    module = imp.load_source(name, filepath)
                except Exception, e:
                    print >> sys.stderr, "Error loading module %s: %s" % (name, e)
                else:
                    self.modules["name"] = module

if __name__ == "__main__":
    dispatch = Dispatch()
    s = server.Server(ADDRESS, dispatch)
    s.serve_forever()
