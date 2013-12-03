#!/usr/bin/env python
import BaseHTTPServer
import cgi
import faulthandler
import json
import urlparse

from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn

class Webserver:
    class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
        pass

    class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def get_wrapper(self):
            return self.server.wrapper

        def address_string(self):
            return str(self.client_address[0])

        def do_GET(s):
            s.do_GETHEAD()

        def do_GETHEAD(s,content=True):
            qd=urlparse.parse_qsl(urlparse.urlparse(s.path).query)
            try:
                if qd:
	                result = s.get_wrapper().get(dict(qd))
		else:
	                result = s.get_wrapper().get(None)
            except NotImplementedError:
                s.send_error(405,'Server does not accept GET / HEAD')
                return
            s.respond(result,content=content)

        def do_HEAD(s):
            s.do_GETHEAD(content=False)

        def respond(s,response,mime='text/html',additional_headers=(),content=True):
            s.send_response(200)
            s.send_header('Content-type', mime)
            s.send_header('Content-length', len(response))
            for (name,value) in additional_headers:
                s.send_header(name,value)
            s.end_headers()
            if content:
                s.wfile.write(response)

        def respond_json(s,response):
            try:
                s.respond(json.dumps(response),'text/json')
            except ValueError:
                s.send_error(500,'Server response was invalid JSON')

        def do_POST(s):
            ctype, pdict = cgi.parse_header(s.headers.getheader('content-type'))
            if ctype == 'text/json':
                try:
                    length = int(s.headers.getheader('content-length'))
                    postdata = s.rfile.read(length)
                    parsedata = json.loads(postdata)
                except ValueError:
                    s.send_error(400,'Invalid JSON sent to server')
                    return

                try:
                    result = self.wrapper().json_transaction(parsedata)
                except NotImplementedError:
                    s.send_error(400,'Server does not accept JSON')
                    return
                s.respond_json(result)

            elif ctype == 'multipart/form-data':
                fs = cgi.FieldStorage( fp = self.rfile, 
                    headers = self.headers, # headers_, 
                    environ={ 'REQUEST_METHOD':'POST' } # all the rest will come from the 'headers' object,	 
                    # but as the FieldStorage object was designed for CGI, absense of 'POST' value in environ	 
                    # will prevent the object from using the 'fp' argument !	 
                )
                try:
                    result = self.wrapper().form_post(fs)
                except NotImplementedError:
                    s.send_error(400,'Server does not accept formdata')
                    return
                s.respond(result)
            else:
                s.send_error(400,'Unknown content POSTed')

    def __init__(self,host_name='',port_number=80):
        self.httpd = Webserver.MultiThreadedHTTPServer((host_name,port_number), Webserver.MyHandler)
        self.httpd.wrapper = self

    def run(self):
        faulthandler.enable()
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        self.httpd.server_close()

    def get(self,form_data):
        return self.html_transaction(form_data)

    def form_post(self,form_data):
        return self.html_transaction(form_data)

    def html_transaction(self,form_data):
        raise NotImplementedError()

    def json_transaction(self,json):
        raise NotImplementedError()

    def head(self,s):
        raise NotImplementedError()

if __name__=='__main__':
	Webserver(port_number=8080).run()
