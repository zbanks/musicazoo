#!/usr/bin/python

from musicazoo.lib.mzbot import MZBot
import sys
import json

if len(sys.argv)>1:
	q=sys.argv[0]
else:
	q='http://localhost:9000'

m=MZBot(q)

while True:
	inp_str=raw_input("> ")
	try:
		inp_json=json.loads(inp_str)
	except ValueError as e:
		print "Bad json:",e
		continue

	try:
		if isinstance(inp_json,dict):
			out_json=m.doCommand(inp_json)
		elif isinstance(inp_json,list):
			out_json=m.doCommands(inp_json)
		else:
			print "Error, please specify a dict or list"
			continue

	except Exception as e:
		print "MZ Error:",e
		continue

	print json.dumps(out_json)
