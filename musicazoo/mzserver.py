#!/usr/bin/env python
import BaseHTTPServer
import cgi
import faulthandler
import hashlib
import hmac
import json
import sys
import os

import musicazoo.settings as settings

from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn

from musicazoo.backgroundmanager import BackgroundManager
from musicazoo.modulemanager import ModuleManager
from musicazoo.mzqueue import MZQueue, MZQueueManager
from musicazoo.staticmanager import StaticManager

HOST_NAME = ''
PORT_NUMBER = 9000

mm=ModuleManager(settings.MODULES)
sm=StaticManager(settings.STATICS)
bm=BackgroundManager(settings.BACKGROUNDS)

q = MZQueue(mm,sm,bm)
qm = MZQueueManager(q)
qm.start()

DEBUG=False

class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
    pass

class MZHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def address_string(self):
        return str(self.client_address[0])

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/json")
        s.end_headers()

    def do_GET(s):
        if DEBUG:
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()
            try:
                print s.path
                if s.path=='/' or s.path=='':
                    s.path='/index.html'
                f = open(os.path.join('../www',s.path[1:]))
                s.wfile.write(f.read())
                f.close()
            except IOError:
                pass
        else:
            s.giveError("Please POST a command.")

    def giveError(s,error):
        s.send_response(200)
        s.send_header("Content-type", "text/json")
        s.end_headers()
        #s.wfile.write(mzqueue.errorPacket(error))

    def do_POST(s):
        """
        ctype, pdict = cgi.parse_header(s.headers.getheader('content-type'))
        if ctype != 'text/json':
            s.giveError("No text/json found.")
            return
        """
        
        length = int(s.headers.getheader('content-length'))
        _owner = s.headers.getheader("X-Auth-Owner")
        signature = s.headers.getheader("X-Auth-Signature")

        postdata = s.rfile.read(length)

        owner = None
        if signature and _owner and _owner in API_KEYS:
            ver_sig = hmac.new(API_KEYS[_owner], postdata, hashlib.sha1).hexdigest()
            print ver_sig, signature
            if ver_sig == signature.lower(): #FIXME: should this be timing-resistant?
                owner = _owner
        
        try:
            parsedata=json.loads(postdata)
        except ValueError:
            s.giveError('Invalid JSON')
            return
        if not isinstance(parsedata,list):
            s.giveError('Input must be a list of commands.')
            return
        
        for cmd in parsedata:
            cmd["_owner"] = owner

        results=q.doMultipleCommandsAsync(parsedata)
        json_output=json.dumps(results)

        s.send_response(200)
        s.send_header("Access-Control-Allow-Origin", "http://localhost:8080")
        s.send_header("Content-type", "text/json")
        s.send_header("Access-Control-Allow-Headers", s.headers.getheader("Access-Control-Request-Headers"))
        s.end_headers()
        s.wfile.write(json_output)

if __name__ == '__main__':
    if '--debug' in sys.argv:
        DEBUG=True

    server_class = MultiThreadedHTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MZHandler)
    faulthandler.enable()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

