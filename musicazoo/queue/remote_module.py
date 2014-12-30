import musicazoo.lib.service as service
import musicazoo.lib.packet as packet
import musicazoo.queue.module as module
import socket
import tornado.iostream
import subprocess
import json

class RemoteModule(module.Module):
    listen_host = "0.0.0.0"
    connect_host = "localhost"

    remote_host = "localhost" 
    remote_port = 8899
    remote_secret = None

    connect_timeout=datetime.timedelta(milliseconds=4000)
    cmd_write_timeout=datetime.timedelta(milliseconds=3000)
    cmd_read_timeout=datetime.timedelta(milliseconds=3000)
    kill_timeout=datetime.timedelta(milliseconds=5000)

    def __init__(self, *args, **kwargs):
        self.detect_host()
        super(RemoteModule, self).__init__(*args, **kwargs)

    def spawn(self):
        additional_args=[self.connect_host,str(self.cmd_port),str(self.update_port)]
        #self.proc=subprocess.Popen(self.process+additional_args)
        command = self.process + additional_args
        result = self.remote_cmd({"cmd": "run", "args": {"command": command}}) #TODO
        self.proc_id = 1 #
        self.alive=True

    # Ensure this module's sub-process is dead
    # Like, no really.
    @service.coroutine
    def terminate_process(self):
        try:
            self.cmd_stream.close()
            self.update_stream.close()
            yield service.with_timeout(self.natural_death_timeout,service.wait(self.proc))
        except (service.TimeoutError, AttributeError):
            print "Module was not dead, sending remote KILL..."
            ##self.proc.terminate()
            self.remote_cmd({"cmd": "kill", "args": {"proc_id": self.proc_id}})
        except Exception:
            print "UNHANDLED EXCEPTION IN TERMINATE"
            traceback.print_exc()
            print "There is probably an orphaned child process!"

    @service.coroutine
    def remote_cmd(self, data):

    def detect_host(self):
        # Connect to the remote host to determine local IP (host)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.remote_host, self.remote_port))
        host = s.getsockname()[0]
        s.close()

        self.listen_host = host
        self.connect_host = host

        return host

