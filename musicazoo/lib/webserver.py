#!/usr/bin/env python
import BaseHTTPServer
import cgi
import faulthandler
import json
import urlparse
import os
import wsgiref
import StringIO

from SocketServer import ThreadingMixIn

CHUNKSIZE=4096

class HTTPException(Exception):
    def __init__(self,num,msg):
        self.http_error_num=num
        self.http_error_msg=msg
        Exception.__init__(self,"{0}: {1}".format(num,msg))

def webserver_app(environ, start_response):
    pass

def make_webserver_json(transaction_fn):
    @middleware_nginx
    @middleware_querystr
    @middleware_json
    def application(environ, start_response, json=None):
        if json is None:
            json = {}
        out_json = transaction_fn({"q":"help"})
        start_response("200 OK", [("Content-type", "text/html")])
        yield "hello"
#return json
    return application

def make_webserver_html(transaction_fn):
    @middleware_nginx
    @middleware_querystr
    def application(environ, start_response):
        out_html = transaction_fn(environ["GET"])
        start_response("200 OK", [("Content-type", "text/html")])
        yield out_html
    return application


def middleware_file(app):
    """
    Milddleware to serve a file response
    Return a tuple of (mime_type, filelike)
    """
    def wrapped(environ, start_response, *args, **kwargs):
        file_mime = None

        file_wrapper = environ.get("wsgi.file_wrapper", wsgiref.util.FileWrapper)

        def wrap_start_response(wr_status, wr_headers):
            headers = wr_headers
            status = wr_status
            # It works, trust me
            if 'Content-type' not in dict(headers):
                headers.append(("Content-type", file_mime))
            start_response(status, headers)

        file_mime, file_obj = app(environ, wrap_start_response, *args, **kwargs)

        return file_wrapper(file_obj)
    return wrapped

def middleware_json(app):
    """
    Middleware to deserialize POST body from JSON, serialize response into JSON
    """
    def wrapped(environ, start_response, *args, **kwargs):
        file_wrapper = environ.get("wsgi.file_wrapper", wsgiref.util.FileWrapper)
        def wrap_start_response(wr_status, wr_headers):
            headers = wr_headers
            status = wr_status

            if 'Content-type' not in dict(headers):
                headers.append(("Content-type", "text/json"))

            start_response(status, headers)

        json_body = json.load(environ["wsgi.input"])

        json_response = app(environ, wrap_start_response, *args, json=json_body, **kwargs)

#sio = StringIO.StringIO()
#json.dump(json_response, sio)
#print json_response, "json"
#wrap_start_response("200 OK", [])
#yield json.dumps(json_response)
#return file_wrapper(sio)
        return json_response
    return wrapped

def middleware_querystr(app):
    """
    Middleware to parse querystrings into environ["GET"]
    """
    def wrapped(environ, start_response, *args, **kwargs):
        # Converting to a dict loses info, but its what fns want.
        environ["GET"] = dict(urlparse.parse_qsl(environ["QUERY_STRING"], True))
        return app(environ, start_response, *args, **kwargs) # I think `return` is okay here
    return wrapped

def middleware_nginx(app):
    """
    Middleware to handle some small nginx fixes (eg IP)
    """
    def wrapped(environ, start_response, *args, **kwargs):
        if "HTTP_X_FORWARDED_FOR" in environ:
            remote_addr = environ["HTTP_X_FORWARDED_FOR"].partition(",")[0].strip()
            environ["REMOTE_ADDR"] = remote_addr
        else:
            remote_addr = environ.get("REMOTE_ADDR", None)

        def wrap_start_response(wr_status, wr_headers):
            headers = wr_headers
            status = wr_status

            if remote_addr is not None:
                headers.append(("Client-ip", remote_addr))

            start_response(status, headers)

        response = app(environ, wrap_start_response, *args, **kwargs)

        return response
    return wrapped


class Webserver:
    #class MultiThreadedHTTPServer(ThreadingMixIn,BaseHTTPServer.HTTPServer): # No threading for testing
    class MultiThreadedHTTPServer(BaseHTTPServer.HTTPServer):
        pass

    class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def get_wrapper(self):
            return self.server.wrapper

        def address_string(self):
            return str(self.client_address[0])

        def do_GET(s):
            s.do_GETHEAD()

        def do_GETHEAD(s,content=True):
            path=urlparse.urlparse(s.path)
            qd=urlparse.parse_qsl(path.query,True)
            try:
                if qd:
	                result = s.get_wrapper().get(dict(qd),path)
		else:
	                result = s.get_wrapper().get(None,path)
            except NotImplementedError:
                s.send_error(405,'Server does not accept GET / HEAD')
                return
            except HTTPException as e:
                s.send_error(e.http_error_num,e.http_error_msg)
                return
            s.respond(result,content=content)

        def do_HEAD(s):
            s.do_GETHEAD(content=False)

        def respond(s,response,*args,**kwargs):
            rf=None
            if isinstance(response,str) or isinstance(response,unicode):
                rf=s.respond_str
            if isinstance(response,file):
                rf=s.respond_file
            if rf is not None:
                return rf(response,*args,**kwargs)
            raise Exception('Unknown type of response')

        def get_client_ip(s):
            if 'X-forwarded-for' in s.headers:
                return s.headers['X-forwarded-for']
            return s.address_string()

        def respond_str(s,response,mime='text/html',additional_headers=(),content=True):
            s.send_response(200)
            s.send_header('Content-type', mime)
            s.send_header('Content-length', len(response))
            s.send_header('Client-ip', s.get_client_ip())
            for (name,value) in additional_headers:
                s.send_header(name,value)
            s.end_headers()
            if content:
                s.wfile.write(response)

        def respond_file(s,response,mime='text/html',additional_headers=(),content=True):
            l=os.fstat(response.fileno()).st_size
            s.send_response(200)
            s.send_header('Content-type', mime)
            s.send_header('Content-length', l)
            s.send_header('Client-ip', s.get_client_ip())
            for (name,value) in additional_headers:
                s.send_header(name,value)
            s.end_headers()

            if content:
                while True:
                    chunk=response.read(CHUNKSIZE)
                    if not chunk:
                        break
                    s.wfile.write(chunk)
            response.close()

        def respond_json(s,response):
            try:
                s.respond_str(json.dumps(response),'text/json')
            except ValueError:
                s.send_error(500,'Server response was invalid JSON')

        def do_POST(s):
            path=urlparse.urlparse(s.path)
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
                    result = s.get_wrapper().json_post(parsedata,path)
                except NotImplementedError:
                    s.send_error(400,'Server does not accept JSON')
                    return
                except HTTPException as e:
                    s.send_error(e.http_error_num,http_error_msg)
                    return
                s.respond_json(result)

            elif ctype == 'multipart/form-data' or ctype == 'application/x-www-form-urlencoded':
                fs = cgi.FieldStorage( fp = s.rfile, 
                    headers = s.headers,
                    environ={ 'REQUEST_METHOD':'POST' }, # all the rest will come from the 'headers' object,	 
                    # but as the FieldStorage object was designed for CGI, absense of 'POST' value in environ	 
                    # will prevent the object from using the 'fp' argument !	 
                    keep_blank_values=True,
                )
                
                fs=dict([(k,fs.getvalue(k)) for k in fs])
                try:
                    result = s.get_wrapper().form_post(fs,path)
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

    def get(self,form_data,path):
        return self.html_transaction(form_data)

    def form_post(self,form_data,path):
        return self.html_transaction(form_data)

    def json_post(self,json,path):
        return self.json_transaction(json)

    def html_transaction(self,form_data):
        raise NotImplementedError()

    def json_transaction(self,json):
        raise NotImplementedError()

    def head(self,s):
        raise NotImplementedError()

if __name__=='__main__':
	Webserver(port_number=8080).run()
