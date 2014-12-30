import json
import sqlite3
import musicazoo.settings as settings

class Database(object):
    def __init__(self, filename=None, log_table=None):
        if filename is None:
            try:
                filename = settings.log_database
            except:
                filename = ":memory:"

        self.conn = sqlite3.connect(filename)
        #XXX check to make sure that log_table is 'safe'
        self.log_table = log_table
        if self.log_table is not None:
            self.create_log_schema()

    def execute(self, _sql_command, **kwargs):
        result = self.conn.execute(_sql_command, kwargs)
        self.conn.commit()
        return result

    def execute_select(self, _sql_command, **kwargs):
        return self.conn.execute(_sql_command, kwargs)

    def log(self, uid, command, response, raw=False):
        if raw:
            input_json = command
            output_json = response
        else:
            input_json = json.dumps(command)
            output_json = json.dumps(response)
        self.execute("INSERT INTO {} (uid, input_json, output_json) VALUES (:uid, :input_json, :output_json);".format(self.log_table),
                     uid=uid, input_json=input_json, output_json=output_json)

    #def queue_log(self, action, target, raw_command=''):
    #    self.execute("INSERT INTO queue (action, target, command) VALUES (:action, :target, :command);",
    #                 action=action, target=target, command=json.dumps(raw_command))

    def create_log_schema(self):
        self.execute("""CREATE TABLE IF NOT EXISTS {} (
            pk INTEGER PRIMARY KEY,
            uid TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            input_json TEXT,
            output_json TEXT
        );""".format(self.log_table))

    def create_top_schema(self):
        """
        (Category --->) Item <---> Module <---> LogEntry

        <---> is a many-to-many relationship
         ---> is a foreign key relationship

        (- Category: represents a group of Items which form a top list)
         - Item: something that can be played multiple times and is grouped by to build a top list
         - Module: an instance of a module on the queue
         - LogEntry: an act performed on the queue and logged
        """
        self.execute("""CREATE TABLE IF NOT EXISTS top_module (
            pk INTEGER PRIMARY KEY,
            uuid TEXT,
            canonical_id TEXT,
            add_timestamp DATETIME
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_category (
            pk INTEGER PRIMARY KEY,
            slug TEXT,
            description TEXT
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_item (
            pk INTEGER PRIMARY KEY,
            category_pk INTEGER,
            requeue_command TEXT,
            url TEXT,
            description TEXT
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_item_module (
            pk INTEGER PRIMARY KEY,
            item_pk INTEGER,
            module_pk INTEGER
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_log_entry (
            pk INTEGER,
            timestamp DATETIME,
            input_json TEXT,
            output_json TEXT
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_module_log_entry (
            pk INTEGER PRIMARY KEY,
            log_pk INTEGER,
            module_pk INTEGER,
            log_type TEXT
        );""")
