import musicazoo.lib.service as service
import os
import signal
import traceback
import socket

class NLP(service.JSONCommandProcessor, service.Service):
    port=5582
    queue_host='localhost'
    queue_port=5580

    def __init__(self):
        print "NLP started."
        super(NLP, self).__init__()

    @service.coroutine
    def queue_cmd(self,cmd,args={}):
        try:
            result = yield service.json_query(self.queue_host,self.queue_port,{"cmd":cmd,"args":args})
        except (socket.error,service.TimeoutError):
            raise Exception("Error communicating with queue.")
        raise service.Return(result)

    @service.coroutine
    def do(self,message):
        #result = yield self.queue_cmd("queue")
        raise service.Return({'message':'Did '+message})

    @service.coroutine
    def suggest(self,message):
        sugs=[message+s for s in [' porn',' weird porn',' creepy porn']]
        raise service.Return({'suggestions':sugs})

    def shutdown(self):
        service.ioloop.stop()

    commands={
        'do': do,
        'suggest': suggest,
    }

nlp = NLP()

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(nlp.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
