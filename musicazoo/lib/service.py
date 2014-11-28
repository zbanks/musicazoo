import tornado.tcpserver
from tornado.gen import *
import itertools
import json
import traceback

@coroutine
def read_until(stream, delimiter, _idalloc=itertools.count()):
    cb_id = next(_idalloc)
    cb = yield Callback(cb_id)
    stream.read_until(delimiter, cb)
    result = yield Wait(cb_id)
    raise Return(result)

def write(stream, data):
    return Task(stream.write, data)

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
        elif isinstanc(line,dict):
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
