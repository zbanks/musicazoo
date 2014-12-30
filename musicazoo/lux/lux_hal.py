import logging
import serial
import time

logger = logging.getLogger(__name__)

class LuxBusDevice(object):
    def __init__(self, port, baudrate=115200, addr=0x00, flags=0x00):
        self.ser = serial.Serial(port, baudrate)
        self.addresses = {}

    def close(self):
        self.ser.close()

    def raw_packet(self, data):
        logger.debug("Serial Data: %s", ';'.join(map(lambda x: "{:02x}".format(x), data)))
        #print ("Serial Data: %s", ';'.join(map(lambda x: "{:02x}".format(x), data)))
        self.ser.write("".join([chr(d) for d in data]))
        return len(data)

    def flush(self):
        self.ser.flush()

    def cobs_packet(self, data):
        #print ("Not encoded: %s", ';'.join(map(lambda x: "{:02x}".format(x), data)))
        rdata = []
        i = 0
        for d in data[::-1]:
            i += 1
            if d == 0:
                rdata.append(i)
                i = 0
            else:
                rdata.append(d)
        return self.raw_packet([0, i+1] + rdata[::-1])
        

    def framed_packet(self, data, addr, flags):

        if data is None or len(data) > 250:
            raise Exception("invalid data")
        data=list(data)
        crc_frame = [addr, flags] + data
        checksum = sum(crc_frame) & 0xff
        frame = [len(data), checksum] + crc_frame
        return self.cobs_packet(frame)

class LuxSingleDevice(object):
    def __init__(self, bus, addr=0x00, flags=0x00):
        self.bus = bus
        self.addr = addr
        self.flags = flags

    def write(self, data):
        return self.bus.framed_packet(data=data, addr=self.addr, flags=self.flags)

class LuxRelayDevice(LuxSingleDevice):
    def __init__(self, size=16, *args, **kwargs):
        self.data_buffer = []
        self.size = size
        self.state = [True] * size
        self.next_state = self.state[:]
        super(LuxRelayDevice, self).__init__(*args, **kwargs)

    def set(self, relay_number, state):
        # 1 -> relay on -> light off
        byte = 0 if state else 1
        byte |= relay_number << 4
        self.data_buffer.append(byte)
        self.next_state[relay_number] = state

    def flush(self, addr=None, flags=None):
        if addr is None:
            addr = self.addr
        if flags is None:
            flags = self.flags

        if self.bus is not None: 
            data_len = self.write(data=self.data_buffer)
        else:
            print("Relay 0x%x:" % addr, self.state)
            data_len = None

        self.data_buffer = []
        self.state = self.next_state[:]
        return data_len

class DummyLuxRelayDevice(object):
    # Deprecated
    def __init__(self, addr=0x00, flags=0x00, size=16):
        self.addr = addr
        self.flags = flags
        self.size = size
        self.state = [True] * size
        self.next_state = self.state[:]

    def set(self, relay_number, state):
        self.next_state[relay_number] = state

    def write(self, addr=None, **kwargs):
        if addr is None:
            addr = self.addr
        self.state = self.next_state[:]
        print "Relay 0x%x:" % addr, self.state


