import math
import lux_hal


class Lux(object):
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

    def get_state(self):
        return {name: self.devices[name].state for name in self.devices}

    def set_state(self, name, relay, new_state):
        name = name.upper()
        if name in self.devices:
            self.devices[name].set(relay, state=new_state)
            self.devices[name].flush()
            return True
        return False

    commands={
        'set_state':set_state
    }

    parameters={
        'state':get_state
    }

    constants={
        'class':'lux'
    }
