#!/usr/bin/env python
import email
import encodings
import json
import os
import quopri
import re
import requests
import sys

class EmailParser:
	def __init__(self,f):
		msg = email.message_from_file(f)
		self.sender = msg["From"]
		self.subject = msg["Subject"]
		self.extra = [] #Youtubes, etc

		for part in msg.walk():
			if part.is_multipart():
				continue
			if part.get_content_type() == "text/plain":
				aliases = encodings.aliases.aliases.keys()
				css=filter(lambda x: x in aliases, part.get_charsets())
				msg=part.get_payload(decode=True)
				msg=re.sub(r'\r\n','\n',msg) # fuck you windows
				msg=self.strip_reply(msg)
				self.body=msg
				self.find_extra(msg)
				break

	def strip_reply(self,msgtxt):
		delims = (
			#r"-- ?\n",
			r"-----Original Message-----",
			r"________________________________",
			r"\nOn [\s\S]+?wrote:\n",
			#r"Sent from my iPhone",
			#r"sent from my BlackBerry",
			#r"\n>"
			)
		for dlm in delims:
			msgtxt = re.split(dlm, msgtxt, 1)[0]
		return msgtxt

	def find_extra(self,msg):
		ytm=re.findall("youtube\.com\/watch\?v=([^&\s]+)",msg)
		for yt in ytm:
			self.extra.append({
				'cmd': 'add',
				'args': {
					'type': 'youtube',
					'args': { 'url': "http://youtube.com/watch?v="+yt }
				}
			})

		if len(self.extra)>3:
			self.extra=self.extra[0:3]

# End class parser

def queue_email(f, queue="http://musicazoo.mit.edu/cmd"):
	ep = EmailParser(f)
	if len(ep.extra):
		duration=3
	else:
		duration=3
	commands = [{
		'cmd': 'add',
		'args': {
			'type': 'text',
			'args': {
				'text': {
					'sender':ep.sender,
					'subject':ep.subject,
					'body':ep.body
				},
				'text_preprocessor': "display_email",
					'speech_preprocessor': "pronounce_email",
				'text2speech': "google",
				'renderer': "email",
				'duration': duration,
				'speed': 1.5,
				'short_description': "Email from {}".format(ep.sender),
				'long_description': "Email from {}".format(ep.sender),
			}
		}
	}]
	commands+=ep.extra
	print requests.post(queue, json.dumps(commands)).text

if __name__ == "__main__":
	if len(sys.argv)==2:
		queue=sys.argv[1]
	else:
		queue="http://localhost/cmd"
	queue_email(sys.stdin,queue=queue) 
