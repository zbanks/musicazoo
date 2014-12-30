import tornado.tcpserver
from tornado.gen import *
from tornado.concurrent import *
import tornado.iostream
import tornado.ioloop
import itertools
import json
import traceback
import time
import musicazoo.lib.packet as packet
from toro import *
import datetime
import socket

ioloop=tornado.ioloop.IOLoop.instance()

@coroutine
def accept(sock):
    @return_future
    def wrap_add_handler(callback):
       def wait_for_accept(fd,events): # TODO more intelligently check for events?
            try:
                result = sock.accept()
                callback(result)
            except socket.error, e:
                if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise

       ioloop.add_handler(sock.fileno(), wait_for_accept, ioloop.READ)

    sock.setblocking(0)
    try:
        result = yield wrap_add_handler()
        raise Return(result)
    finally:
        ioloop.remove_handler(sock.fileno())

@coroutine
def wait(proc):
    poll_period=datetime.timedelta(milliseconds=10)
    while True:
        p=proc.poll()
        if p is not None:
            raise Return(p)

        @return_future
        def pause(callback):
            ioloop.add_timeout(poll_period,callback)

        yield pause()

def connection_ready(sock, fd, events):
    while True:
        try:
            connection, address = sock.accept()
        except socket.error, e:
            if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise
            return
        connection.setblocking(0)
        handle_connection(connection, address)

@coroutine
def listen_for_commands(stream,handle_cr,over_fn=None):
    try:
        while True:
            data = yield stream.read_until('\n')
            parsed = json.loads(data)
            response = yield handle_cr(parsed)
            encoded = json.dumps(response)+'\n'
            yield stream.write(encoded)
    except tornado.iostream.StreamClosedError:
        pass
    except Exception:
        print "Communication exception!"
        traceback.print_exc()
        print "(communication interrupted)"
    finally:
        stream.close()
    if over_fn:
        over_fn()

@coroutine
def json_query(addr,port,inp,timeout=2):
    @coroutine
    def talk(stream):
        yield stream.connect((addr,port))
        encoded = json.dumps(inp)+'\n'
        yield stream.write(encoded)
        data = yield stream.read_until('\n')
        decoded = json.loads(data)
        raise Return(decoded)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    stream = tornado.iostream.IOStream(s)
    try:
        result = yield with_timeout(datetime.timedelta(seconds=timeout),talk(stream))
    finally:
        stream.close()
    raise Return(result)

class Service(tornado.tcpserver.TCPServer):
    def __init__(self,port=None):
        if port is not None:
            self.port = port
        tornado.tcpserver.TCPServer.__init__(self)
        self.listen(self.port)

    # Override this
    @coroutine
    def command(self,query):
        raise Return(query)

    def handle_stream(self,stream,address):
        return listen_for_commands(stream,self.command)

class JSONCommandProcessor(object):
    @coroutine
    def command(self,line):
        if isinstance(line,list):
            try:
                result=[]
                for c in line:
                    single_result=yield self.single_command(c)
                    result.append(single_result)
            except Exception:
                traceback.print_exc()
                result = packet.error("Generic multi-command processing error")
            finally:
                raise Return(result)
        elif isinstance(line,dict):
            try:
                result = yield self.single_command(line)
            except Exception:
                traceback.print_exc()
                result = packet.error("Generic command processing error")
            finally:
                raise Return(result)
        else:
            raise Return(packet.error("Command must be either dict (single command) or list (multiple commands)"))

    # Parse and run a command
    @coroutine
    def single_command(self,line):
        if not isinstance(line,dict):
            raise Return(packet.error('Command not a dict.'))

        try:
            cmd=line['cmd'] # Fails if no cmd given
        except KeyError:
            raise Return(packet.error('No command given.'))

        try:
            args=line['args']
        except KeyError:
            args={}

        if not isinstance(args,dict):
            raise Return(packet.error('Argument list not a dict.'))

        try:
            f=self.commands[cmd]
        except KeyError:
            raise Return(packet.error('Bad command.'))

        try:
            result=yield f(self,**args)
            result=packet.good(result)
        except Exception as e:
            traceback.print_exc()
            result=packet.error(str(e))

        if cmd in self.log_cmds and self.logger:
            #self.logger.log({'timestamp':str(datetime.datetime.utcnow()),'id':self.log_prefix,'sent':line,'received':result})
            self.logger.log(None, line, result)

        raise Return(result)

    commands = {}
    log_cmds = []
    log_prefix = None
    logger = None
