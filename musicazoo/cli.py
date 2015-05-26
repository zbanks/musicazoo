#!/usr/bin/env python2

import json
import os
import sys
import urllib
import urllib2

endpoint = os.environ.get("MZ_ENDPOINT", "http://musicazoo.mit.edu/nlp")

m=' '.join(sys.argv[1:])

json_req={"cmd":"do","args":{"message":m}}

req = urllib2.Request(endpoint)
req.add_header('Content-type', 'text/json')
req.data=json.dumps(json_req)

handler = urllib2.urlopen(req)
result=json.loads(handler.read())
if result['success']:
    print result['result']
else:
    print "error:", result['error']
