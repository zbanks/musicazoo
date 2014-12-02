import tornado.ioloop
import musicazoo.queue
from musicazoo.queue.modules import youtube,problem

modules = [youtube.Youtube,problem.Problem]

musicazoo.queue.Queue(modules)
tornado.ioloop.IOLoop.instance().start()
