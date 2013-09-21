#!/usr/bin/env python
#grodytothemax

import BaseHTTPServer
import cgi
import json
import magic
import os
import urlparse
import requests
import re

HOST_NAME = ''
PORT_NUMBER = 9003

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

MZQ_URL='http://musicazoo.mit.edu/cmd'

def youtube_lucky_args(match, kw):
    # Return the args dict for the first youtube result for 'match'
    youtube_req_url = "http://gdata.youtube.com/feeds/api/videos"
    youtube_data = {
        "v": 2,
        "orderby": "relevance",
        "alt": "jsonc",
        "q": match,
        "max-results": 5
    }
    youtube_data = requests.get(youtube_req_url, params=youtube_data).json()
    try:
        return {
            "url": "http://youtube.com/watch?v=%s" % youtube_data["data"]["items"][0]["id"],
        }
    except KeyError, IndexError:
        return None

COMMANDS = [
    {   # say, text - say & display text
        "keywords": ("text", "say"),
        "module": "text",
        "args": lambda match, kw:
            {
                "text": match,
                "text_preprocessor": "none",
                "speech_preprocessor": "pronunciation",
                "text2speech": "google",
                "renderer": "splash",
                "duration": 1,
                "short_description": "(Text)",
                "long_description": "Text: %s" % match,
            }
    },
    {   # netvid - play a network video
        "keywords": ("netvid", ),
        "module": "netvid",
        "args": lambda match, kw:
            {
                "url": match,
                "short_description": "Network Video",
                "long_description": match,
            }
    },
    {   # youtube - play a youtube video
        "keywords": ("youtube", "video", "vimeo"),
        "module": "youtube",
        "regex": re.compile(r"/.*youtube.com.*watch.*v.*/"),
        "args": lambda match, kw: { "url": match }
    },
    {   # image - show an image as a background
        "keywords": ("image", "img"),
        "regex": re.compile(r"http.*(gif|jpe?g|png|bmp)"),
        "module": "image",
        "type": "background",
        "args": lambda match, kw: {"url": match}
    },
    {   # logo - show the logo
        "keywords": ("logo"),
        "module": "logo",
        "type": "background",
        "args": lambda match, kw: {}
    },
    {   # youtube auto search
        "regex": re.compile(r".*"),
        "module": "youtube",
        "args": youtube_lucky_args,
    },
]


class MultiThreadedHTTPServer(ThreadingMixIn,HTTPServer):
	pass

def command_match(commands, text):
    ADD_CMDS = {
        'background': 'set_bg',
        'static': 'set_static',
        'module': 'add',
        None: 'add',
    }
    text = text.strip()
    kw, _, rest = text.partition(" ")
    match = None
    for cmd in commands:
        if cmd.get("keywords"):
            if kw in cmd['keywords']:
                match = rest
                break
        if cmd.get("regex"):
            regex = re.match(cmd.get("regex"), rest)
            if regex:
                match = regex.group()
                break
    else:
        return False
    add_cmd = ADD_CMDS[cmd.get("type")]
    args = cmd["args"](match, kw)
    if args is None:
        return False
    return [{
        "cmd": add_cmd, 
        "args": {
            "type": cmd["module"],
            "args": args,
        }
    }]

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def address_string(self):
		return str(self.client_address[0])

	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Content-type", "application/json")
		s.end_headers()

	def parse(self,q):
		parsed_command = command_match(COMMANDS, q)
		print parsed_command
		if parsed_command:
			return self.req(parsed_command)
		g=re.compile(r'vol (\d\d?\d?)').match(q)
		if g:
			try:
				vol=int(g.group(1))
				if vol>100:
					raise Exception
				scap=self.req([{'cmd':'static_capabilities'}])[0]
				if not scap['success']:
					raise Exception
				vol_i=None
				for (i,static) in scap['result'].iteritems():
					if static['class']=='volume':
						vol_i=i
				if not vol_i:
					raise Exception
				resp=self.req([
				{
					"cmd": "tell_static", "args":
					{
						"uid": vol_i,
						"cmd": "set_vol",
						"args": {"vol": vol}
					}
				}])
			except:
				pass

	def do_GET(s):
		qd=urlparse.parse_qsl(urlparse.urlparse(s.path).query)
		if not qd:
			return
		q=dict(qd)['q']
		s.act(q)
		
	def do_POST(s):
		ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))	 
		if ctype == 'multipart/form-data':
			fs = cgi.FieldStorage( fp = self.rfile, 
				headers = self.headers, # headers_, 
				environ={ 'REQUEST_METHOD':'POST' } # all the rest will come from the 'headers' object,	 
				# but as the FieldStorage object was designed for CGI, absense of 'POST' value in environ	 
				# will prevent the object from using the 'fp' argument !	 
			)
		else:	
			raise Exception('Unexpected post request')

		q=fs['q'].value
		s.act(q)

	def act(s,q):
		try:
			commands=s.parse(q)
		except Exception as e:
			s.send_error(500,str(e))
			return
		s.send_response(200)
		s.send_header("Content-type", "application/json")
		s.end_headers()
		s.wfile.write("{'success':true}")

	def req(s,commands):
		return json.loads(requests.post(MZQ_URL, json.dumps(commands)).text)

if __name__ == '__main__':
	server_class = MultiThreadedHTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

