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
        print "New Connection:", host, cmd_port, update_port
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

    # Sends response to a command
    def send_resp(self,packet):
        p_str=json.dumps(packet)+'\n'
        self.cs.send(p_str)

    # Gracefully close the open sockets
    def close(self):
        self.cs.close()
        self.us.close()

class JSONParentPoller(object):
    def __init__(self):
        self.connection = ParentConnection()

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
            
            if response is not None:
                self.connection.send_resp(response)

