import json
import sqlite3
import musicazoo.settings as settings

class Database(object):
    def __init__(self, filename=None):
        if filename is None:
            try:
                filename = settings.log_database
            except:
                filename = ":memory:"

        self.conn = sqlite3.connect(filename)
        self.create_schema()

    def execute(self, _sql_command, **kwargs):
        result = self.conn.execute(_sql_command, kwargs)
        self.conn.commit()
        return result

    def execute_select(self, _sql_command, **kwargs):
        return self.conn.execute(_sql_command, kwargs)

    def queue_log(self, action, target, raw_command=''):
        self.execute("INSERT INTO queue (action, target, command) VALUES (:action, :target, :command);",
                     action=action, target=target, command=json.dumps(raw_command))

    def create_queue_schema(self):
        self.execute("""CREATE TABLE IF NOT EXISTS queue_log (
            pk INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            json TEXT
        );""")

    def create_top_schema(self):
        """
        Category ---> Item <---> Module <---> LogEntry

        <---> is a many-to-many relationship
         ---> is a foreign key relationship

         - Category: represents a group of Items which form a top list
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
            json TEXT
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_module_log_entry (
            pk INTEGER PRIMARY KEY,
            log_pk INTEGER,
            module_pk INTEGER,
            log_type TEXT
        );""")
