import musicazoo.lib.service as service
import os
import signal
import math

try:
    import alsaaudio
except:
    alsaaudio = None

try:
    import osax
except:
    osax = None

exp=0.6 # approximate

def human_to_computer(val):
	return int(100*(float(val)/100)**exp)

def computer_to_human(val):
	return int(100*(float(val)/100)**(1.0/exp))

class Volume(service.JSONCommandService):
    port=5581

    def __init__(self):
        print "Volume started."

        if alsaaudio:
            self.mixer=alsaaudio.Mixer(control='PCM')
        elif osax:
            self.mixer = osax.OSAX()
        else:
            print "Unable to control volume"

        # JSONCommandService handles all of the low-level TCP connection stuff.
        super(Volume, self).__init__()

    @service.coroutine
    def get_vol(self):
        if alsaaudio:
            v=self.mixer.getvolume()[0]
        elif osax:
            v=self.mixer.get_volume_settings()[osax.k.output_volume]
        else:
            v=0
        raise service.Return({'vol': computer_to_human(v)})

    @service.coroutine
    def set_vol(self,vol):
        v=human_to_computer(vol)
        if alsaaudio:
            self.mixer.setvolume(v)
        elif osax:
            self.mixer.set_volume(output_volume=v)
        else:
            pass
        raise service.Return({})

    def shutdown(self):
        service.ioloop.stop()

    commands={
        'set_vol': set_vol,
        'get_vol': get_vol
    }

vol = Volume()

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(vol.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
