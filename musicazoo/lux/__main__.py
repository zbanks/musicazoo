import json
import math
import musicazoo.lib.packet as packet
import musicazoo.lib.service as service
import musicazoo.settings as settings
import signal

import lux_hal


class Lux(service.JSONCommandProcessor, service.Service):
    port=settings.ports["lux"]

    DEVICES = {
        # Name : (Address, Size)
        "G": (0x30, 10),
        "B": (0x31, 10),
        "W": (0x32, 0),
    }
    def __init__(self):
        for i in range(10):
            try:
                self.bus = lux_hal.LuxBusDevice(port="/dev/ttyUSB%d" % i)
            except Exception as e:
                print i, e
                pass
            else:
                break
        else:
            self.bus = None
            print "No lux bus found; mocking"

        self.devices = {}
        for name, (addr, size) in self.DEVICES.items():
            name = name.upper()
            self.devices[name] = lux_hal.LuxRelayDevice(bus=self.bus, size=size, addr=addr, flags=0xFF)

        super(Lux, self).__init__()

    @service.coroutine
    def get_state(self):
        raise service.Return({name: self.devices[name].state for name in self.devices})

    @service.coroutine
    def set_state(self, name, relay, new_state):
        name = name.upper()
        if name in self.devices:
            self.devices[name].set(relay, state=new_state)
            self.devices[name].flush()
            raise service.Return(True)
        raise service.Return(False)

    def shutdown(self):
        service.ioloop.stop()

    commands={
        'set_state':set_state,
        'get_state':get_state,
    }

lux = Lux()

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(vol.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
