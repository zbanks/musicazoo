import musicazoo.lib.service as service
import musicazoo.lib.tcp
import musicazoo.lib.packet as packet
import socket
import tornado.iostream
import tornado.ioloop
import subprocess
import json

class Module(object):
    listen_host = 'localhost'
    connect_host = 'localhost'

    def __init__(self,remove_function):
        self.parameters={}
        self.remove_function=remove_function
        self.cmd_lock = service.Lock()

    # Set up listening sockets for subprocess
    def listen(self):
        self.cmd_port = musicazoo.lib.tcp.get_free_port()
        self.update_port = musicazoo.lib.tcp.get_free_port()

        s1=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.bind((self.listen_host,self.cmd_port))
        s1.listen(1)
        s2=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((self.listen_host,self.update_port))
        s2.listen(1)
        return [service.accept(s1),service.accept(s2)]

    # Launch subprocess
    def spawn(self):
        additional_args=[self.connect_host,str(self.cmd_port),str(self.update_port)]
        self.proc=subprocess.Popen(self.process+additional_args)
        self.alive=True

    # Set up IOstreams for the command and update connection objects
    def setup_connections(self,connections):
        conn1,conn2=tuple(connections)
        self.cmd_stream = tornado.iostream.IOStream(conn1[0])
        self.cmd_stream.set_close_callback(self.on_disconnect)

        self.update_stream = tornado.iostream.IOStream(conn2[0])
        self.update_stream.set_close_callback(self.on_disconnect)

    @service.coroutine
    def new(self,args=None):
        listen_futures = self.listen()
        self.spawn()
        connections = yield listen_futures
        self.setup_connections(connections)
        self.poll_updates()
        self.is_on_top=False
        result = yield self.send_cmd("init",args)

    @service.coroutine
    def remove(self):
        yield self.send_cmd("rm")
        yield self.external_terminate()

    @service.coroutine
    def play(self):
        yield self.send_cmd("play")
        self.is_on_top=True

    @service.coroutine
    def suspend(self):
        yield self.send_cmd("suspend")
        self.is_on_top=False

    @service.coroutine
    def send_cmd(self,cmd,args=None):
        cmd_dict={"cmd":cmd}
        if args is not None:
            cmd_dict["args"]=args
        cmd_str=json.dumps(cmd_dict)+'\n'

        with (yield self.cmd_lock.acquire()):
            yield service.write(self.cmd_stream,cmd_str)
            response_str = yield service.read_until(self.cmd_stream,'\n')

        response_dict=json.loads(response_str)
        packet.assert_success(response_dict)
        if 'result' in response_dict:
            raise service.Return(response_dict['result'])

    def on_disconnect(self):
        if self.alive:
            print "OH NO, child died!"
            service.ioloop.add_future(self.internal_terminate(),self.terminate_done)

    def terminate_done(self,f):
        print "done killing child",f

    # Terminated by queue, don't need to remove self
    def external_terminate(self):
        return self.terminate()

    @service.coroutine
    def terminate(self):
        # TODO implement nice timeouts and stuff and make this asynchronous
        if not self.alive:
            raise service.Return()
        self.cmd_stream.close()
        self.update_stream.close()
        if self.proc.poll() is None: # TODO wait .1 sec here
            self.proc.terminate()
            if self.proc.poll() is None: # TODO wait 1 sec here
                self.proc.kill()
        self.alive=False

    # Terminated naturally, need to inform queue
    @service.coroutine
    def internal_terminate(self):
        yield self.terminate()
        yield self.remove_function()

    def poll_updates(self):
        self.update_stream.read_until('\n',self.got_update)

    def got_update(self,data):
        print "RECEIVED DATA!"
        print data[:-1]
        self.poll_updates()

    def get_multiple_parameters(self,parameters):
        return dict([(p,self.parameters[p]) for p in parameters if p in self.parameters])

    @service.coroutine
    def tell(self,cmd,args):
        result = yield self.send_cmd("do_"+cmd,args)
        raise service.Return(result)

# For the sub-process
class ParentConnection():
    def __init__(self):
        import socket
        import sys

        host = sys.argv[1]
        cmd_port = int(sys.argv[2])
        update_port = int(sys.argv[3])
        self.cs=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.us=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.cs.connect((host,cmd_port))
        self.us.connect((host,update_port))

        self.cs_buffer=''
        self.us_buffer=''

    def recv_cmd(self):
        while True:
            self.cs_buffer+=self.cs.recv(4096)
            a=self.cs_buffer.find('\n')
            if a >= 0:
                cmd=self.cs_buffer[0:a]
                self.cs_buffer=self.cs_buffer[a+1:]
                break
        return json.loads(cmd)

    def send_resp(self,packet):
        p_str=json.dumps(packet)+'\n'
        self.cs.send(p_str)

    def close(self):
        self.cs.close()
        self.us.close()
