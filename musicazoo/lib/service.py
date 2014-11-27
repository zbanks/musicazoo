import tornado.tcpserver
from tornado.gen import *
import itertools
import json

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
        except Exception as e:
            print "Exception occurred!" # json exception
        finally:
            stream.close()

