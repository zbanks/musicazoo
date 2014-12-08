import musicazoo.lib.service as service
import os
import signal
import traceback
import socket
import re
import musicazoo.lib.packet as packet

class NLP(service.JSONCommandProcessor, service.Service):
    port=5582
    queue_host='localhost'
    queue_port=5580

    vol_host='localhost'
    vol_port=5581

    pretty_params={'youtube':['title']}

    def __init__(self):
        print "NLP started."
        super(NLP, self).__init__()

    @service.coroutine
    def queue_cmd(self,cmd,args={},assert_success=True):
        try:
            result = yield service.json_query(self.queue_host,self.queue_port,{"cmd":cmd,"args":args})
        except (socket.error,service.TimeoutError):
            raise Exception("Error communicating with queue.")
        if assert_success:
            raise service.Return(packet.assert_success(result))
        raise service.Return(result)

    @service.coroutine
    def vol_cmd(self,cmd,args={},assert_success=True):
        try:
            result = yield service.json_query(self.vol_host,self.vol_port,{"cmd":cmd,"args":args})
        except (socket.error,service.TimeoutError):
            raise Exception("Error communicating with volume control.")
        if assert_success:
            raise service.Return(packet.assert_success(result))
        raise service.Return(result)

    @service.coroutine
    def do(self,message):
        message=message.strip()
        for (regex,func) in self.nlp_commands:
            m=re.match(regex,message,re.I)
            if m:
                result = yield func(self,message,*m.groups())
                raise service.Return(result)
        raise Exception("Command not recognized.")

    #result = yield self.queue_cmd("queue")
        raise service.Return({'message':'Did '+message})

    @service.coroutine
    def suggest(self,message):
        sugs=[message+s for s in [' porn',' weird porn',' creepy porn']]
        raise service.Return({'suggestions':sugs})

    def shutdown(self):
        service.ioloop.stop()

    @service.coroutine
    def cmd_set_vol(self,q,vol):
        if vol=='up':
            result=yield self.vol_cmd("get_vol")
            vol=min(result['vol']+5,100)
        elif vol=='down':
            result=yield self.vol_cmd("get_vol")
            vol=max(result['vol']-5,0)
        else:
            vol=int(vol)

        if vol>100:
            raise Exception("Volume cannot be greater than 100")
        yield self.vol_cmd("set_vol",{"vol":vol})

        raise service.Return("Volume set to {0}".format(vol))

    @service.coroutine
    def cmd_get_vol(self,q):
        result=yield self.vol_cmd("get_vol")
        raise service.Return("Volume is {0}".format(result))

    @service.coroutine
    def cmd_queue(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise service.Return("Queue is empty!")
        result = '\n'.join(["{0}. {1}".format(n+1,self.pretty(mod)) for (n,mod) in zip(range(len(queue)),queue)])
        raise service.Return(result)

    @service.coroutine
    def cmd_rm_top(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise service.Return("Queue is empty!")
        mod=queue[0]
        yield self.queue_cmd("rm",{"uids":[mod['uid']]})
        raise service.Return("Removed {0}".format(self.pretty(mod)))

    @service.coroutine
    def cmd_rm_bot(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise service.Return("Queue is empty!")
        mod=queue[-1]
        yield self.queue_cmd("rm",{"uids":[mod['uid']]})
        raise service.Return("Removed {0}".format(self.pretty(mod)))

    @service.coroutine
    def cmd_bump(self,q):
        queue=yield self.queue_cmd("queue",{"parameters":self.pretty_params})
        if len(queue)==0:
            raise service.Return("Queue is empty!")
        if len(queue)==1:
            raise service.Return("Only one thing on the queue!")
        old_uids=[mod['uid'] for mod in queue]
        mod_bot=queue[-1]
        new_uids=old_uids[-1:]+old_uids[0:-1]
        yield self.queue_cmd("mv",{"uids":[mod['uid']]})
        raise service.Return("Bumped {0} to the top".format(self.pretty(mod_bot)))

    def pretty(self,mod):
        print mod
        t=mod['type']
        if t=='youtube' and 'title' in mod['parameters']:
            return u'"{0}"'.format(mod['parameters']['title'])
        #if t=='netvid':
        #    return u'{0}'.format(mod['parameters']['short_description'])
        #if t=='text':
        #    return u'{0}'.format(mod['parameters']['short_description'])
        return t

    @service.coroutine
    def cmd_help(self,q):
        raise service.Return("""Commands I understand:
help|? - This
vol - Get volume
vol [num] - Set volume
vol up|down - Change volume
stop|stfu|skip|next - Remove the top video
pop|undo|oops - Remove the bottom video
bump - Move the bottom video to the top
q|queue - List the queue
Anything else - Queue Youtube video
""")

    commands={
        'do': do,
        'suggest': suggest,
    }

    nlp_commands=[
        (r'^help$',cmd_help),
        (r'^$',cmd_help),
        (r'^\?$',cmd_help),
        (r'^vol (\d+|up|down)$',cmd_set_vol),
        (r'^vol$',cmd_get_vol),
        (r'^stop$',cmd_rm_top),
        (r'^stfu$',cmd_rm_top),
        (r'^skip$',cmd_rm_top),
        (r'^next$',cmd_rm_top),
        (r'^pop$',cmd_rm_bot),
        (r'^undo$',cmd_rm_bot),
        (r'^oops$',cmd_rm_bot),
        (r'^bump$',cmd_bump),
        (r'^q$',cmd_queue),
        (r'^queue$',cmd_queue),
        #(r'^(.+)$',cmd_yt),
    ]

nlp = NLP()

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(nlp.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
