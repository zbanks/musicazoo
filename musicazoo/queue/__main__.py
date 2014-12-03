import musicazoo.queue
import musicazoo.lib.service as service
from musicazoo.queue.modules import youtube,problem
import signal

modules = [youtube.Youtube,problem.Problem]

#modules = {
#   "youtube": ["python", "path/to/youtube.py"],
#}


q=musicazoo.queue.Queue(modules)

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(q.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
