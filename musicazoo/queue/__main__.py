import tornado.ioloop
import musicazoo.queue
from musicazoo.queue.modules import youtube,problem

modules = [youtube.Youtube,problem.Problem]

#modules = {
#   "youtube": ["python", "path/to/youtube.py"],
#}

musicazoo.queue.Queue(modules)
tornado.ioloop.IOLoop.instance().start()
