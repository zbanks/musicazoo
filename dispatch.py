import server
import re
import imp
import json
import threading
import os

# Address of dispatcher on network. (Address, Port)
ADDRESS = ('', 6785)
# Resources available to be used by queue items
RESOURCES = set(["audio", "screen"])
# Location of modules
MODULES_DIR = "/etc/musicazoo/modules/"

class Queue:

class Dispatch:
    """
    Dispatch

    Reads in JSON objects over socket and dispatches commands,
    manages queue, and switches between program modules.
    """


if __name__ == "__main__":
    dispatch = Dispatch()
    s = server.Server(ADDRESS, dispatch)
    s.serve_forever()
