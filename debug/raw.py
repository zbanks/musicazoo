#!/usr/bin/python

import sys
import json
import readline
import requests

if len(sys.argv)>1:
	endpoint=sys.argv[1]
else:
	endpoint='http://localhost:8080/vol'

def do_command(cmd_list):
    json_data = json.dumps(cmd_list)
    headers = {"Content-type": "text/json"}
    resp = requests.post(endpoint, data=json_data, headers=headers)
    if resp.status_code != 200:
        raise IOError(resp.text)
    return resp.json()

while True:
	inp_str=raw_input("> ")
	try:
		inp_json=json.loads(inp_str)
	except ValueError as e:
		print "Bad json:",e
		continue

	try:
		if isinstance(inp_json,dict):
			out_json=do_command(inp_json)
		elif isinstance(inp_json,list):
			out_json=do_command(inp_json)
		else:
			print "Error, please specify a dict or list"
			continue

	except Exception as e:
		print "MZ Error:",e
		continue

	print json.dumps(out_json)
