import json
import sqlite3

class Database(object):
    def __init__(self, filename=":memory:"):
        self.conn = sqlite3.connect(filename)
        self.create_schema()

    def execute(self, command, **kwargs):
        return self.conn.execute(command, kwargs)

    def queue_log(self, action, target, raw_command=''):
        self.execute("INSERT INTO queue (action, target, command) VALUES (:action, :target, :command);",
                     action=action, target=target, command=json.dumps(raw_command))

    def create_schema(self):
        self.execute("""CREATE TABLE IF NOT EXISTS queue (
            pk INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            command TEXT,
            target TEXT,
            action TEXT
        );""")
