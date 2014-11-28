import tornado.ioloop
import musicazoo.queue
musicazoo.queue.Queue()
tornado.ioloop.IOLoop.instance().start()
