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
import musicazoo.lib.database as database

class Top(service.JSONCommandProcessor, service.Service):
    port=5583
    queue_host='localhost'
    queue_port=5580

    MAX_COUNT = 100

    def __init__(self):
        print "Top started."
        self.queue_db = database.Database()
        self.db = database.Database()
        super(Top, self).__init__()

    def import_queue_log(self):
        row = self.db.execute_select("SELECT pk FROM top_log_entry ORDER BY pk DESC LIMIT 1").fetchone()
        if row is None:
            last_pk = -1
        else:
            last_pk = row["pk"]

        rows = self.queue_db.execute_select("SELECT pk, timestamp, uid, input_json, output_json FROM queue_log WHERE pk > :last_pk ORDER BY pk ASC", last_pk=last_pk)
        for row in rows:
            input_json = json.parse(row["input_json"])
            output_json = json.parse(row["output_json"])
            uid = row["uid"]
            if not uid:
                # Queue command
                related_uuids = []
                if json_data["cmd"] == "add":
                    pass
            else:
                # Instance command
                pass


    @service.coroutine
    def cmd_list(self, offset=0, count=100):
        count = max(min(self.MAX_COUNT, count), 1)

        rows = self.db.execute_select(
                'SELECT COUNT(*) as plays, target, command FROM queue GROUP BY target ORDER BY plays DESC, timestamp DESC LIMIT :offset, :count',
                offset=offset, count=count)

        last_rank = offset + 1
        last_plays = None
        results = []

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
