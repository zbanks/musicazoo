import tornado.tcpserver
from tornado.gen import *
import tornado.ioloop
import itertools
import json
import traceback
import time

# TODO Callback, Wait are deprecated
@coroutine
def read_until(stream, delimiter, _idalloc=itertools.count()):
    cb_id = next(_idalloc)
    cb = yield Callback(cb_id)
    stream.read_until(delimiter, cb)
    result = yield Wait(cb_id)
    raise Return(result)

def write(stream, data):
    return Task(stream.write, data)

# TODO Callback, Wait are deprecated, and timeout doesn't work because of this
# also this could probably be rewritten to be nicer
@coroutine
def accept(sock, timeout=None, _idalloc=itertools.count()):
    cb_id = next(_idalloc)
    cb = yield Callback(cb_id)
    sock.setblocking(0)
    io_loop = tornado.ioloop.IOLoop.instance()
    callback = functools.partial(cb, sock)
    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
    if timeout is not None:
        end_t=time.time()+timeout
    try:
        while True:
            if timeout is not None:
                t=time.time()
                if t >= end_t:
                    raise Exception("Timeout occurred.")
                yield with_timeout(end_t-t,Wait(cb_id))
            else:
                yield Wait(cb_id)
            try:
                result = sock.accept()
                break
            except socket.error, e:
                if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise
                continue
    finally:
        io_loop.remove_handler(sock.fileno())
    raise Return(result)

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

    @coroutine
    def handle_stream(self,stream,address):
        try:
            data = yield read_until(stream,'\n')
            parsed = json.loads(data)
            response = yield self.command(parsed)
            encoded = json.dumps(response)+'\n'
            yield write(stream, encoded)
        except Exception:
            print "Communication exception!"
            traceback.print_exc()
            print "(communication interrupted)"
        finally:
            stream.close()

class JSONCommandService(Service):
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
                result = error_packet("Generic multi-command processing error")
            finally:
                raise Return(result)
        elif isinstance(line,dict):
            try:
                result = yield self.single_command(line)
            except Exception:
                traceback.print_exc()
                result = error_packet("Generic command processing error")
            finally:
                raise Return(result)
        else:
            raise Return(error_packet("Command must be either dict (single command) or list (multiple commands)"))

    # Parse and run a command
    @coroutine
    def single_command(self,line):
        if not isinstance(line,dict):
            raise Return(error_packet('Command not a dict.'))

        try:
            cmd=line['cmd'] # Fails if no cmd given
        except KeyError:
            raise Return(error_packet('No command given.'))

        try:
            args=line['args']
        except KeyError:
            args={}

        if not isinstance(args,dict):
            raise Return(error_packet('Argument list not a dict.'))

        try:
            f=self.commands[cmd]
        except KeyError:
            raise Return(error_packet('Bad command.'))

        try:
            result=yield f(self,**args)
        except Exception as e:
            traceback.print_exc()
            raise Return(error_packet(str(e)))

        raise Return(good_packet(result))

    commands={
    }

def error_packet(err):
    return {'success':False,'error':err}

def good_packet(payload):
    if payload is not None:
        return {'success':True,'result':payload}
    return {'success':True}
