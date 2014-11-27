from musicazoo.lib.service import Service

class MZQueue(Service):
    port=5580

import tornado.ioloop
MZQueue()
tornado.ioloop.IOLoop.instance().start()
