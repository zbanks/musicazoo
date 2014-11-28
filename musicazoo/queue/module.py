import musicazoo.lib.service as service
import musicazoo.lib.tcp
import socket
import tornado.iostream
import subprocess

class Module(object):
    listen_host = 'localhost'
    connect_host = 'localhost'

    def __init__(self):
        self.parameters={}

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

    # Set up IOstreams for the command and update connection objects
    def setup_connections(self,connections):
        conn1,conn2=tuple(connections)
        self.cmd_stream = tornado.iostream.IOStream(conn1[0])
        self.cmd_stream.set_close_callback(self.on_disconnect)

        self.update_stream = tornado.iostream.IOStream(conn2[0])
        self.update_stream.set_close_callback(self.on_disconnect)

    @service.coroutine
    def new(self,args):
        listen_futures = self.listen()
        self.spawn()
        connections = yield listen_futures
        self.setup_connections(connections)

        self.poll_updates()

    def on_disconnect(self):
        print "OH NO, child died!"
        self.cmd_stream.close()
        self.update_stream.close()

    def poll_updates(self):
        self.update_stream.read_until('\n',self.got_update)

    def got_update(self,data):
        print "RECEIVED DATA!"
        print data[:-1]
        self.poll_updates()

    def get_multiple_parameters(self,parameters):
        return dict([(p,self.parameters[p]) for p in parameters if p in self.parameters])

    @service.coroutine
    def tell(self,cmd,parameters):
        raise service.Return()
