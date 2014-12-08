#!/usr/bin/env python2

import urllib
import urllib2
import json
import sys

endpoint="http://localhost:8080/nlp"

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
    print result['error']
