import musicazoo.lib.service as service
import musicazoo.lib.tcp
import musicazoo.lib.packet as packet
import socket
import tornado.iostream
import tornado.ioloop
import subprocess
import json

# A module is an object on the queue.
# The actual code for a module runs in a sub-process.
# This class contains the infrastructure for starting, stopping, and communicating with that sub-process.

# TODO add appropriate locking so that a module that is in the process of being shutdown doesn't receive additional commands

class Module(object):
    # Hostname for listening socket
    # i.e. "Who is allowed to connect to the queue?"
    listen_host = 'localhost'
    # Hostname for connecting socket (passed to sub-process)
    # i.e. "Where does the queue process live?"
    connect_host = 'localhost'

    # Make a new instance of this module.
    # This constructor is fairly bare because it is not a coroutine.
    # Most of the object initialization is done in new()
    def __init__(self,remove_function):
        self.parameters={}
        self.remove_function=remove_function
        self.cmd_lock = service.Lock()

    # Helper function for new()
    # Set up listening sockets for subprocess
    def listen(self):
        self.cmd_port = musicazoo.lib.tcp.get_free_port()
        print "Command port:", self.cmd_port
        s1=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.bind((self.listen_host,self.cmd_port))
        s1.listen(0)

        self.update_port = musicazoo.lib.tcp.get_free_port()
        print "Update port:", self.update_port
        s2=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((self.listen_host,self.update_port))
        s2.listen(0)
        return [service.accept(s1),service.accept(s2)]

    # Helper function for new()
    # Launch subprocess
    def spawn(self):
        additional_args=[self.connect_host,str(self.cmd_port),str(self.update_port)]
        self.proc=subprocess.Popen(self.process+additional_args)
        self.alive=True

    # Helper function for new()
    # Set up IOstreams for the command and update connection objects
    def setup_connections(self,connections):
        conn1,conn2=tuple(connections)
        self.cmd_stream = tornado.iostream.IOStream(conn1[0])
        self.cmd_stream.set_close_callback(self.on_disconnect)

        self.update_stream = tornado.iostream.IOStream(conn2[0])
        self.update_stream.set_close_callback(self.on_disconnect)

    # Handles the majority of object initialization
    # Waits for socket communication to be established
    # and for the initialization command to return successfully
    @service.coroutine
    def new(self,args=None):
        # Set up two sockets for communication with the sub-process
        listen_futures = self.listen()
        # Launch the subprocess
        self.spawn()

        # Wait for the subprocess to connect
        connections = yield listen_futures
        self.setup_connections(connections)

        # Set up a callback for push-notifications from the sub-process
        self.poll_updates()

        # Helps the queue keep track of whether a module is playing or suspended
        self.is_on_top=False

        # Send initialization data to the sub-process
        result = yield self.send_cmd("init",args)

    # Called from queue
    # Stops the module, as it has been removed from the queue
    @service.coroutine
    def remove(self):
        yield self.send_cmd("rm")
        yield self.external_terminate()

    # Called from queue
    # Plays the module, as it has reached the top of the queue
    @service.coroutine
    def play(self):
        yield self.send_cmd("play")
        self.is_on_top=True

    # Called from queue
    # Suspends the module, as it has been bumped down from the top of the queue
    @service.coroutine
    def suspend(self):
        yield self.send_cmd("suspend")
        self.is_on_top=False

    # Called by queue
    # Retrieve some cached parameters
    def get_multiple_parameters(self,parameters):
        return dict([(p,self.parameters[p]) for p in parameters if p in self.parameters])

    # Called by queue
    # Issues a custom command to the module sub-process
    @service.coroutine
    def tell(self,cmd,args):
        result = yield self.send_cmd("do_"+cmd,args)
        raise service.Return(result)

    # Send a command to the sub-process over the command pipe
    @service.coroutine
    def send_cmd(self,cmd,args=None):
        cmd_dict={"cmd":cmd}
        if args is not None:
            cmd_dict["args"]=args
        cmd_str=json.dumps(cmd_dict)+'\n'

        # Lock on the command pipe so we ensure sequential req/rep transactions
        with (yield self.cmd_lock.acquire()):
            yield service.write(self.cmd_stream,cmd_str)
            response_str = yield service.read_until(self.cmd_stream,'\n')

        response_dict=json.loads(response_str)
        packet.assert_success(response_dict)
        if 'result' in response_dict:
            raise service.Return(response_dict['result'])

    # Callback for if either pipe gets terminated
    def on_disconnect(self):
        # Unused callback
        def terminate_done(f):
            print "done killing child"

        if self.alive:
            # If the process was presumed alive, shut it down 
            print "OH NO, child died!"
            # This counts as an internal termination as it is still on the queue
            service.ioloop.add_future(self.internal_terminate(),terminate_done)

    # The queue removed this module, ensure it is completely shutdown
    # No other behaviour is necessary
    def external_terminate(self):
        return self.terminate()

    # This module terminated independently of the queue
    # Ensure it is completely shutdown, and then remove it from the queue
    @service.coroutine
    def internal_terminate(self):
        yield self.terminate()
        yield self.remove_function()

    # Ensure this module's sub-process is dead
    # Like, no really.
    @service.coroutine
    def terminate(self):
        # TODO implement nice timeouts and stuff and make this asynchronous
        if not self.alive:
            raise service.Return()
        self.cmd_stream.close()
        self.update_stream.close()
        if self.proc.poll() is None: # TODO wait .1 sec here
            print "Module was not dead, sending SIGTERM..."
            self.proc.terminate()
            if self.proc.poll() is None: # TODO wait 1 sec here
                print "Module was not dead, sending SIGKILL..."
                self.proc.kill()
        self.alive=False

    # Register callback for data received on this module's update pipe
    def poll_updates(self):
        self.update_stream.read_until('\n',self.got_update)

    # Callback for when data received on this module's update pipe
    def got_update(self,data):
        print "RECEIVED DATA!" # TODO update this module's parameters dictionary
        print data[:-1]
        self.poll_updates() # re-register


