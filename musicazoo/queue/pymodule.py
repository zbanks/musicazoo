import json
import socket
import sys
import threading
import traceback

import musicazoo.lib.packet as packet

# Modules can be written in any language, but if you choose to write them in python.
# you may find the contents of this file helpful.

# Connects back to the queue based on command-line arguments
class ParentConnection(object):
    def __init__(self):
        host = sys.argv[-3]
        cmd_port = int(sys.argv[-2])
        update_port = int(sys.argv[-1])
        self.cs=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.us=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.cs.connect((host,cmd_port))
        self.us.connect((host,update_port))

        self.cs_buffer=''
        self.us_buffer=''

    # Blocks until a command has been received and returns it
    def recv_cmd(self):
        while True:
            self.cs_buffer+=self.cs.recv(4096)
            a=self.cs_buffer.find('\n')
            if a >= 0:
                cmd=self.cs_buffer[0:a]
                self.cs_buffer=self.cs_buffer[a+1:]
                break
        return json.loads(cmd)

    # Blocks until an update has been acknowledged
    def recv_update_resp(self):
        while True:
            self.us_buffer+=self.us.recv(4096)
            a=self.us_buffer.find('\n')
            if a >= 0:
                resp=self.us_buffer[0:a]
                self.us_buffer=self.us_buffer[a+1:]
                break
        resp_dict = json.loads(resp)
        packet.assert_success(resp_dict)
        return resp_dict['result']

    # Sends response to a command
    def send_resp(self,packet):
        p_str=json.dumps(packet)+'\n'
        self.cs.send(p_str)

    # Sends an update packet
    def send_update(self, packet):
        p_str=json.dumps(packet)+'\n'
        self.us.send(p_str)
        # Right now, updates are not responded to
        #return self.recv_update_resp()

    # Gracefully close the open sockets
    def close(self):
        self.cs.close()
        self.us.close()

class JSONParentPoller(object):
    def __init__(self):
        self.connection = ParentConnection()
        self.update_lock = threading.Lock()
        super(JSONParentPoller,self).__init__()

    def serialize(self):
        return {}

    def close(self):
        return self.connection.close()

    def handle_one_command(self):
        data = self.connection.recv_cmd()
        try:
            if 'cmd' not in data:
                raise Exception("Malformed command")

            cmd=data['cmd']

            if cmd not in self.commands:
                print "Unrecognized command:", cmd, data
                raise Exception("Unrecognized command")

            cmd_f=self.commands[cmd]

            args = data.get("args", {})

            self.connection.send_resp(packet.good(cmd_f(self,**args)))

        except Exception as e:
            traceback.print_exc()
            self.connection.send_resp(packet.error(str(e)))

    def update(self, params=None):
        with self.update_lock:
            if params is None:
                params = self.serialize()
            data = {"cmd": "set_parameters", "args": {"parameters": params}}
            return self.connection.send_update(data)

    def update_rm(self):
        with self.update_lock:
            data = {"cmd": "rm"}
            return self.connection.send_update(data)
