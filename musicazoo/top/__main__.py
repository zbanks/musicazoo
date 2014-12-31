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
        self.db.create_top_schema()
        super(Top, self).__init__()

    def import_queue_log(self):
        row = self.db.execute_select("SELECT pk FROM top_log_entry ORDER BY pk DESC LIMIT 1").fetchone()
        if row is None:
            last_pk = -1
        else:
            last_pk = row["pk"]

        rows = self.queue_db.execute_select("SELECT pk, timestamp, uid, input_json, output_json FROM queue_log WHERE pk > :last_pk ORDER BY pk ASC", last_pk=last_pk)

        def copylog(row):
            rd = database.row_dict(row)
            self.db.execute(
                "INSERT INTO top_log_entry (pk, timestamp, uid, input_json, output_json) VALUES (:pk, :timestamp, :uid, :input_json, :output_json)",
                **rd)

        rowcount = rows.rowcount

        for row in rows:
            input_data = json.loads(row["input_json"])
            output_data = json.loads(row["output_json"])
            uid = row["uid"]
            log_pk = row["pk"]

            if not uid:
                # Queue command
                if not output_data.get("success"):
                    continue

                copylog(row)

                if input_data["cmd"] == "add":
                    added_uid = output_data["result"]["uid"]
                    self.db.execute(
                        "INSERT INTO top_module (add_timestamp, uuid) VALUES (:timestamp, :uuid)",
                        timestamp=row["timestamp"], uuid=added_uid)
                    self.db.execute(
                            "INSERT INTO top_module_log_entry (module_uuid, log_pk, log_type) VALUES (:uuid, :log_pk, :ltype)",
                            uuid=added_uid, log_pk=log_pk, ltype="queue_add")
                    self.process_new_module(added_uid, input_data)
                elif input_data["cmd"] == "rm":
                    rmed_uids = input_data["args"]["uids"]
                    for ruid in rmed_uids:
                        self.db.execute(
                                "INSERT INTO top_module_log_entry (module_uuid, log_pk, log_type) VALUES (:uuid, :log_pk, :ltype)",
                                uuid=ruid, log_pk=log_pk, ltype="queue_rm")
            else:
                # Instance command
                if not output_data.get("success"):
                    continue

                if input_data["cmd"] == "init":
                    copylog(row)
                    self.db.execute(
                            "INSERT INTO top_module_log_entry (module_uuid, log_pk, log_type) VALUES (:uuid, :log_pk, :ltype)",
                            uuid=uid, log_pk=log_pk, ltype="module_init")
                elif input_data["cmd"] == "play":
                    copylog(row)
                    self.db.execute(
                            "INSERT INTO top_module_log_entry (module_uuid, log_pk, log_type) VALUES (:uuid, :log_pk, :ltype)",
                            uuid=uid, log_pk=log_pk, ltype="module_play")

                if input_data["cmd"] == "set_parameters":
                    pass
                elif input_data["cmd"] == "unset_parameters":
                    pass
                elif input_data["cmd"] == "rm":
                    copylog(row)
                    self.db.execute(
                            "INSERT INTO top_module_log_entry (module_uuid, log_pk, log_type) VALUES (:uuid, :log_pk, :ltype)",
                            uuid=uid, log_pk=log_pk, ltype="module_rm")
        self.db.commit()
        return rowcount

    def process_new_module(self, uuid, add_cmd):
        add_type = add_cmd["args"].get("type")
        add_args = add_cmd["args"].get("args", {})

        if add_type == "youtube":
            url = add_args.get("url")
            canonical_id = "youtube|{}".format(url)
            description = None

            row = self.db.execute_select(
                "SELECT pk FROM top_item WHERE canonical_id = :cid LIMIT 1",
                cid=canonical_id).fetchone()
            if row is not None:
                item_pk = row["pk"]
            else:
                item_pk = self.db.execute(
                        "INSERT INTO top_item (canonical_id, url, description, requeue_command) VALUES (:cid, :url, :desc, :cmd)",
                    cid=canonical_id, url=url, desc=description, cmd=json.dumps(add_cmd)).lastrowid
            self.db.execute(
                "INSERT INTO top_item_module (item_pk, module_uuid) VALUES (:pk, :uuid)",
                pk=item_pk, uuid=uuid)

    @service.coroutine
    def cmd_list(self, offset=0, count=100):
        count = max(min(self.MAX_COUNT, count), 1)

        rows = self.db.execute_select(
            """SELECT
                    COUNT(top_item_module.module_uuid) AS playcount,
                    top_item.requeue_command AS requeue_command,
                    top_item.url AS url,
                    top_item.description AS description
                FROM top_item_module
                INNER JOIN top_item
                    ON top_item.pk = top_item_module.item_pk
                GROUP BY top_item_module.item_pk
                ORDER BY playcount DESC
                LIMIT :offset, :count
            """, offset=offset, count=count)

        last_rank = offset + 1
        last_plays = None
        results = []

        for i, row in enumerate(rows):
            print row
            if row["playcount"] == last_plays:
                rank = last_rank
            else:
                rank = offset + 1 + i
                last_rank = rank
                last_plays = row["playcount"]
            results.append({
                'url': row['url'],
                'description': row['description'],
                'command': row['requeue_command'],
                'queue_count': row['playcount'],
                'play_count': row['playcount'], #TODO
                'rank': rank,
            })

        raise service.Return(results)

    @service.coroutine
    def cmd_queue(self,message):
        raise service.Return("Not Implemented")

    @service.coroutine
    def cmd_vote(self,message):
        raise service.Return("Not Implemented")

    @service.coroutine
    def cmd_update(self):
        #TODO: this is a temp fix until daemonized properly
        rc = self.import_queue_log()
        raise service.Return("Updated {} records".format(rc))

    def shutdown(self):
        service.ioloop.stop()

    commands={
        'list': cmd_list,
        'queue': cmd_queue,
        'vote': cmd_vote,
        'update': cmd_update
    }

top = Top()

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(top.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
