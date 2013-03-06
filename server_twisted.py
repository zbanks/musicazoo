#!/usr/bin/python

import logging
import uuid
import json

from twisted.protocols.amp import AMP
from twisted.internet import reactor
from twisted.internet.protocol import Factory, ServerFactory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.application.service import Application
from twisted.application.internet import StreamServerEndpointService

from commands import *
from module_list import ModuleList

logging.basicConfig(level=logging.DEBUG, format="%(created)-15s %(msecs)d %(levelname)8s %(thread)d %(name)s %(message)s")
log                        = logging.getLogger(__name__)

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
        self.state = state or PlaybackState(self.resources)
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
                output.append(copy.deepcopy(act.status()))
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
            self.stop(activity, killed=False) #killed=True)
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

    def remove_all(self):
        for act in self.running.values():
            self.stop(act)
        for act in self.queue:
            self.stop(act)
        self.refresh()
    
    def remove_activity(self, m_id):
        if m_id in self.running:
            self.stop(self.running[m_id])
        for act in self.queue:
            # Gahh, so inefficient :-(
            if act.status()["id"] == m_id:
                self.stop(act)
                break
            """
            # Errors should propogate to AMP call; don't catch errors here
            try:
                if act.status()["id"] == m_id:
                    self.stop(act)
                    break
            except Exception, err:
                print >> sys.stderr, "Error getting status"
                print >> sys.stderr, err
            """
        self.refresh()


def create_activity(module, m_id, jsondata):
    jsondata["id"] = m_id
    return module(jsondata)

class DispatchProtocol(AMP):
    def __init__(self, *args, **kwargs):
        AMP.__init__(self, *args, **kwargs)
        self.module_list = ModuleList(MODULES_DIR)
        self.interface = PlaybackInterface()

    @PushModule.responder
    def push_module(self, module, _jsondata):
        jsondata = json.loads(_jsondata)
        module = module.lower()
        if not self.module_list.exists(module):
            raise NotImplementedError("Module %s does not exist" % module)
        m_id = str(uuid.uuid1())

        try:
            activity = create_activity(self.module_list.get(module), m_id, jsondata)
        except Exception as err:
            raise ModuleError("Error initializing module %s" % module)

        failed = self.interface.enque(activity)
        if failed:
            raise ModuleError("Error enquing module %s" % module)

        return {"id": m_id}

    @MessageModule.responder
    def message_module(self, m_id, message, _jsondata):
        jsondata = json.loads(_jsondata)
        raise NotImplementedError

    @Reload.responder
    def reload(self):
        self.module_list.reload()

    @RemoveActivity.responder
    def remove_activity(self):
        self.interface.remove_activity()

    @RemoveAll.responder
    def remove_all(self):
        self.interface.remove_all()

    @Status.responder
    def status(self):
        def fmt_json(m):
            return {"id": m["id"],
                    "module": "NotImplemented",
                    "jsondata": json.dumps(m) }

        return {"volume": 0, #TODO
                "playing": [fmt_json(m) for m in self.interface.playing()],
                "queue": [fmt_json(m) for m in self.interface.queued()] }
                              


class DispatchFactory(ServerFactory)
    protocol = DispatchProtocol

if __name__ == "__main__":
    application = Application("musicazoo dispatch")

    endpoint = TCP4ServerEndpoint(reactor, 8750)
    factory = ServerFactory()
    service = StreamServerEndpointService(endpoint, factory)
    service.setServiceParent(application)
