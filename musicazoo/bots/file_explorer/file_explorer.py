#!/usr/bin/env python

import BaseHTTPServer
import cgi
import json
import magic
import os

HOST_NAME = ''
PORT_NUMBER = 8888

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

MOUNTS = {'home': '/Users/zbanks', 'tmp': '/tmp'}

#class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
class MultiThreadedHTTPServer(HTTPServer):
    pass

class FileExplorerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def address_string(self):
        return str(self.client_address[0])

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.end_headers()

    def do_GET(s):
        s.send_response(200)
        if s.path == "/":
            s.send_header("Content-type", "text/html")
            s.end_headers()
            with open('files.html') as f:
                s.wfile.write(f.read())
            return

        s.send_header("Content-type", "application/json")
        s.end_headers()

        files = []

        _mount, _, _path = s.path.partition(":/")  
        mount = _mount.strip(":/ ").lower()
        print _mount, _path
        if mount in MOUNTS:
            path = os.path.join(MOUNTS[mount], _path)
            if path[-1] == '/':
                path = path[:-1]
            if os.path.realpath(path) == path and path.startswith(MOUNTS[mount]):
                md = magic.Magic()
                print "PATH", path
                for ld in os.listdir(path):
                    try:
                        lpath = os.path.join(path, ld)
                        pub_lpath = os.path.join(s.path, ld) #"/{}:{}".format(mount, _path)
                        if os.path.islink(lpath):
                            pass
                        elif os.path.isdir(lpath):
                            f = {'name': ld,
                                 'path': pub_lpath,
                                 'type': 'DIR',
                                 'num_files': len(os.listdir(lpath)),
                                 'size': os.path.getsize(lpath),
                                 'atime': os.path.getatime(lpath),
                                 'ctime': os.path.getctime(lpath),
                                }
                            files.append(f)
                        elif os.path.isfile(lpath):
                            f = {'name': ld,
                                 'path': pub_lpath,
                                 'type': 'FILE',
                                 'size': os.path.getsize(lpath),
                                 'atime': os.path.getatime(lpath),
                                 'ctime': os.path.getctime(lpath),
                                 'magic': md.from_file(lpath),
                                }
                            files.append(f)
                    except:
                        pass
            else:
                print os.path.realpath(path),'p', path, "NO MATCH"
        else:
            print mount, MOUNTS, "No mount"

        s.wfile.write(json.dumps(files))

    def do_POST(s):
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.end_headers()
        s.wfile.write("{}")

if __name__ == '__main__':
    server_class = MultiThreadedHTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), FileExplorerHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
