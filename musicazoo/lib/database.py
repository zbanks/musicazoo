import json
import sqlite3
import musicazoo.settings as settings

def row_dict(r):
    # Convert a sqlite3.Row object to a dictionary
    return {k: r[k] for k in r.keys()}
        
class Database(object):
    def __init__(self, filename=None, log_table=None):
        if filename is None:
            try:
                filename = settings.log_database
            except:
                filename = ":memory:"

        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = sqlite3.Row
        #XXX check to make sure that log_table is 'safe'
        self.log_table = log_table
        if self.log_table is not None:
            self.create_log_schema()

    def execute(self, _sql_command, **kwargs):
        return self.conn.execute(_sql_command, kwargs)

    def execute_select(self, _sql_command, **kwargs):
        return self.execute(_sql_command, **kwargs)

    def commit(self):
        return self.conn.commit()

    def log(self, uid, namespace, command, response, raw=False):
        if raw:
            input_json = command
            output_json = response
        else:
            input_json = json.dumps(command)
            output_json = json.dumps(response)
        self.execute("INSERT INTO {} (uid, namespace, input_json, output_json) VALUES (:uid, :nspace, :input_json, :output_json);".format(self.log_table),
                     uid=uid, nspace=namespace, input_json=input_json, output_json=output_json)

        self.commit()

    #def queue_log(self, action, target, raw_command=''):
    #    self.execute("INSERT INTO queue (action, target, command) VALUES (:action, :target, :command);",
    #                 action=action, target=target, command=json.dumps(raw_command))

    def create_log_schema(self):
        self.execute("""CREATE TABLE IF NOT EXISTS {} (
            pk INTEGER PRIMARY KEY,
            uid TEXT,
            namespace TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            input_json TEXT,
            output_json TEXT
        );""".format(self.log_table))
        self.commit()

    def destroy_top_schema(self):
        self.execute("DROP TABLE IF EXISTS top_module")
        self.execute("DROP TABLE IF EXISTS top_module_item")
        self.execute("DROP TABLE IF EXISTS top_category")
        self.execute("DROP TABLE IF EXISTS top_item")
        self.execute("DROP TABLE IF EXISTS top_log_entry")
        self.execute("DROP TABLE IF EXISTS top_module_log_entry")
        self.commit()

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
            uuid TEXT,
            add_timestamp DATETIME
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_category (
            pk INTEGER PRIMARY KEY,
            slug TEXT,
            description TEXT
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_item (
            pk INTEGER PRIMARY KEY,
            canonical_id TEXT,
            category_pk INTEGER,
            requeue_command TEXT,
            url TEXT,
            description TEXT
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_item_module (
            pk INTEGER PRIMARY KEY,
            item_pk INTEGER,
            module_uuid TEXT
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_log_entry (
            pk INTEGER,
            uid TEXT,
            namespace TEXT,
            timestamp DATETIME,
            input_json TEXT,
            output_json TEXT
        );""")
        self.execute("""CREATE TABLE IF NOT EXISTS top_module_log_entry (
            pk INTEGER PRIMARY KEY,
            log_pk INTEGER,
            module_uuid TEXT,
            log_type TEXT
        );""")
        self.commit()
