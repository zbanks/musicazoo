import tornado.ioloop
import musicazoo.queue
from musicazoo.queue.modules import youtube

modules = [youtube.Youtube]

musicazoo.queue.Queue(modules)
tornado.ioloop.IOLoop.instance().start()
