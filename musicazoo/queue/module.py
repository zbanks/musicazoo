import musicazoo.lib.service as service
import musicazoo.lib.packet as packet
import socket
import tornado.iostream
import subprocess
import json
import datetime
import traceback

# A module is an object on the queue.
# The actual code for a module runs in a sub-process.
# This class contains the infrastructure for starting, stopping, and communicating with that sub-process.

class Module(service.JSONCommandProcessor):
    # Hostname for listening socket
    # i.e. "Who is allowed to connect to the queue?"
    listen_host = 'localhost'
    # Hostname for connecting socket (passed to sub-process)
    # i.e. "Where does the queue process live?"
    connect_host = 'localhost'

    connect_timeout=datetime.timedelta(milliseconds=2000)
    cmd_write_timeout=datetime.timedelta(milliseconds=1000)
    cmd_read_timeout=datetime.timedelta(milliseconds=1000)
    natural_death_timeout=datetime.timedelta(milliseconds=3000) # give SIGTERM after 1 sec
    sigterm_timeout=datetime.timedelta(milliseconds=5000) # give SIGKILL after 1 sec

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
        s1=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.bind((self.listen_host, 0))
        s1.listen(0)
        self.cmd_port = s1.getsockname()[1]
        s2=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((self.listen_host, 0))
        s2.listen(0)
        self.update_port = s2.getsockname()[1]
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
        #self.cmd_stream.set_close_callback(self.on_disconnect)

        self.update_stream = tornado.iostream.IOStream(conn2[0])
        #self.update_stream.set_close_callback(self.on_disconnect)

    # Handles the majority of object initialization
    # Waits for socket communication to be established
    # and for the initialization command to return successfully
    @service.coroutine
    def new(self,args=None):
        # Set up two sockets for communication with the sub-process
        listen_futures = self.listen()
        # Launch the subprocess
        self.spawn()

        try:
            # Wait for the subprocess to connect
            try:
                connections = yield [service.with_timeout(self.connect_timeout,f) for f in listen_futures]
            except service.TimeoutError:
                raise Exception("Could not connect to spawned module")
            self.setup_connections(connections)

            # Helps the queue keep track of whether a module is playing or suspended
            self.is_on_top=False

            # Send initialization data to the sub-process
            try:
                result = yield self.send_cmd("init",args)
            except service.TimeoutError:
                raise Exception("Could not init spawned module")
        except Exception:
            self.terminate() # ensure process is dead if any sort of error occurs
            raise

        def poll_updates_done(f):
            if f.exception() is not None:
                traceback.print_exception(*f.exc_info())

        service.ioloop.add_future(self.poll_updates(),poll_updates_done) # Listen for updates from module forever

    # Called from queue
    # Stops the module, as it has been removed from the queue
    @service.coroutine
    def remove(self):
        yield self.send_cmd("rm")
        self.terminate()

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

        toe=None
        # Lock on the command pipe so we ensure sequential req/rep transactions
        try:
            with (yield self.cmd_lock.acquire()):
                yield service.with_timeout(self.cmd_write_timeout,self.cmd_stream.write(cmd_str))
                response_str = yield service.with_timeout(self.cmd_read_timeout,self.cmd_stream.read_until('\n'))
        except (service.TimeoutError,tornado.iostream.StreamClosedError) as e:
            self.terminate()
            if isinstance(e,service.TimeoutError):
                raise Exception("Timeout sending message to module")
            if isinstance(e,tornado.iostream.StreamClosedError):
                raise Exception("Pipe to module unexpectedly closed")
            raise

        response_dict=json.loads(response_str)
        raise service.Return(packet.assert_success(response_dict))

    # Callback for if either pipe gets terminated
    #def on_disconnect(self):
    #    # Unused callback
    #    def terminate_done(f):
    #        if f.exception() is not None:
    #            traceback.print_exception(*f.exc_info())
    #        print "done killing child"

    #    if self.alive:
    #        # If the process was presumed alive, shut it down 
    #        print "OH NO, child died!"
    #        # This counts as an internal termination as it is still on the queue
    #        service.ioloop.add_future(self.internal_terminate(),terminate_done)

    # This function schedules a module's death and returns immediately.
    # It also removes the module from the queue if it is on it.
    def terminate(self):
        if self.alive:
            self.alive=False

            def remove_from_queue_done(f):
                pass

            def terminate_process_done(f):
                pass

            service.ioloop.add_future(self.remove_function(),remove_from_queue_done)
            service.ioloop.add_future(self.terminate_process(),terminate_process_done)

    # Ensure this module's sub-process is dead
    # Like, no really.
    @service.coroutine
    def terminate_process(self):
        try:
            self.cmd_stream.close()
            self.update_stream.close()
            yield service.with_timeout(self.natural_death_timeout,service.wait(self.proc))
        except (service.TimeoutError, AttributeError):
            print "Module was not dead, sending SIGTERM..."
            self.proc.terminate()
            try:
                yield service.with_timeout(self.sigterm_timeout,service.wait(self.proc))
            except service.TimeoutError:
                print "Module was not dead, sending SIGKILL..."
                self.proc.kill()
        except Exception:
            print "UNHANDLED EXCEPTION IN TERMINATE"
            traceback.print_exc()
            print "There is probably an orphaned child process!"

    # Poll for updates forever
    def poll_updates(self):
        return service.listen_for_commands(self.update_stream,self.command,self.terminate)

    @service.coroutine
    def set_parameters(self,parameters):
        self.parameters.update(parameters)

    @service.coroutine
    def unset_parameters(self,parameters):
        for parameter in parameters:
            self.parameters.pop(parameter, None)

    commands={
        'set_parameters':set_parameters,
        'unset_parameters':unset_parameters,
        'rm':service.coroutine(terminate),
    }

