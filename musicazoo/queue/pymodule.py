import json
import socket
import sys
import traceback

import musicazoo.lib.packet as packet

# Modules can be written in any language, but if you choose to write them in python.
# you may find the contents of this file helpful.

# Connects back to the queue based on command-line arguments
class ParentConnection(object):
    def __init__(self):
        host = sys.argv[1]
        cmd_port = int(sys.argv[2])
        update_port = int(sys.argv[3])
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
        return self.recv_update_resp()

    # Gracefully close the open sockets
    def close(self):
        self.cs.close()
        self.us.close()

class JSONParentPoller(object):
    def __init__(self):
        self.connection = ParentConnection()

    def serialize(self):
        return {}

    def close(self):
        return self.connection.close()

    def poller(self):
        while True:
            data = self.connection.recv_cmd()
            print "Module Recieved: ", data
            cmd = "cmd_" + data.get("cmd")

            if not hasattr(self, cmd):
                response = packet.error("Invalid command")
            else:
                args = data.get("args", {})

                try:
                    response = getattr(self, cmd)(**args)
                except Exception:
                    traceback.print_exc()
                    response = packet.error("Generic multi-command processing error")
            
            self.connection.send_resp(response)

    def update(self):
        params = self.serialize()
        data = {"cmd": "set_parameters", "args": [params]}
        return self.send_update(data)
