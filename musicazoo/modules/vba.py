import evdev
import subprocess
import threading
import time

E = evdev.ecodes

class FakeKeyboard(object):
    def __init__(self, keys):
        self.keys = keys
        events = {E.EV_KEY: keys.values()}
        self.uinput = evdev.uinput.UInput(events=events)

    def key_down(self, k):
        if k in self.keys:
            self.uinput.write(E.EV_KEY, self.keys[k], 1)
            self.uinput.syn()

    def key_up(self, k):
        if k in self.keys:
            self.uinput.write(E.EV_KEY, self.keys[k], 0)
            self.uinput.syn()

class VBA(object):
    TYPE_STRING='vba'
    VBA_KEYS = {
        "up": E.KEY_UP,
        "down": E.KEY_DOWN,
        "left": E.KEY_LEFT,
        "right": E.KEY_RIGHT,
        "a": E.KEY_Z,
        "b": E.KEY_X,
        "l": E.KEY_A,
        "r": E.KEY_S,
        "start": E.KEY_ENTER,
        "select": E.KEY_BACKSPACE,
        "turbo": E.KEY_SPACE,
        #"capture": E.KEY_F12,
    }

    def __init__(self,queue,uid):
        self.queue = queue
        self.uid = uid
        self.vbam = None
        self.events = FakeKeyboard(self.VBA_KEYS)
        self.keys_down = set()
        self.lock = threading.Lock()
        self.keylock = threading.Lock()
        self.lock.acquire()

    def play(self):
        #self.vbam = subprocess.Popen(["/home/musicazoo/vbam", "-c", "/home/musicazoo/vbam.cfg"])
        self.vbam = subprocess.Popen(["/usr/local/bin/mednafen", "/home/musicazoo/roms/gold.gbc"], env={"MEDNAFEN_HOME", "/home/musicazoo/.mednafen/"})
        self.lock.acquire()

    def stop(self):
        if self.vbam is not None:
            self.vbam.terminate() # VBA-M won't stop on terminate
            time.sleep(5)
            self.vbam.kill()
        self.lock.release()

    def key_down(self, key):
        self.keylock.acquire()
        if key not in self.keys_down:
            self.events.key_down(key) 
            self.keys_down.add(key)
        self.keylock.release()

    def key_up(self, key):
        self.keylock.acquire()
        if key in self.keys_down:
            self.events.key_up(key) 
            self.keys_down.remove(key)
        self.keylock.release()

    def status(self):
        if self.vbam is None:
            return "starting"
        self.vbam.poll()
        if self.vbam.returncode is None:
            return "playing"
        self.stop()
        return "stopped"

    commands={
        'stop':stop,
        'key_down': key_down,
        'key_up': key_up
    }

    parameters={
        'status': status,
        'keys': lambda s: s.VBA_KEYS.keys(),
        'keys_down': lambda s: list(s.keys_down),
    }
