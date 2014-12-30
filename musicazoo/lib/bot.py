#!/usr/bin/env python2

import urllib
import urllib2
import json
import sys

DEFAULT_ENDPOINT = "http://localhost:8080/queue"

def request(message, endpoint=DEFAULT_ENDPOINT):
    req = urllib2.Request(endpoint)
    req.add_header('Content-type', 'text/json')
    req.data=json.dumps(message)

    handler = urllib2.urlopen(req)
    result=json.loads(handler.read())
    if result['success']:
        return result['result']
    else:
        raise Exception(result['error'])
