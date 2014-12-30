import json
import os
import re
import signal
import socket
import tornado.httpclient
import traceback
import urllib

import musicazoo.lib.database as database
import musicazoo.lib.packet as packet
import musicazoo.lib.service as service

class Top(service.JSONCommandProcessor, service.Service):
    port=5583
    queue_host='localhost'
    queue_port=5580

    MAX_COUNT = 100

    def __init__(self):
        print "Top started."
        self.db = database.Database()
        super(Top, self).__init__()

    @service.coroutine
    def cmd_list(self, offset=0, count=100):
        count = max(min(self.MAX_COUNT, count), 1)

        rows = self.db.execute_select(
                'SELECT COUNT(*) as plays, target, command FROM queue GROUP BY target ORDER BY plays DESC, timestamp DESC LIMIT :offset, :count',
                offset=offset, count=count)

        last_rank = offset + 1
        last_plays = None
        results = []

        print "ROWS", rows, rows.fetchone()

        for i, row in enumerate(rows):
            print row
            if row["plays"] == last_plays:
                rank = last_rank
            else:
                rank = offset + i
                last_rank = rank
                last_plays = row["plays"]
            results.append({
                'target': row['target'],
                'command': row['command'],
                'queue_count': row['plays'],
                'play_count': row['plays'], #TODO
                'rank': rank,
            })

        raise service.Return(results)

    @service.coroutine
    def cmd_queue(self,message):
        raise service.Return("Not Implemented")

    @service.coroutine
    def cmd_vote(self,message):
        raise service.Return("Not Implemented")

    def shutdown(self):
        service.ioloop.stop()

    commands={
        'list': cmd_list,
        'queue': cmd_queue,
        'vote': cmd_vote,
    }

top = Top()

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(top.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
