#!/usr/bin/env python
import email
import encodings
import json
import os
import quopri
import re
import sys
import talon
import urllib2

#talon.init()

def send_mz_commands(endpoint, commands):
    req = urllib2.Request(endpoint)
    req.add_header('Content-type', 'text/json')
    req.data=json.dumps(commands)

    handler = urllib2.urlopen(req)
    result=json.loads(handler.read())
    return result

class EmailParser(object):
    def parse(self,f):
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
        main_message = talon.quotations.extract_from_plain(msgtxt)
        #text, signature = talon.signature.extract(main_message, self.sender)
        #return text
        return main_message

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

    def queue_email(self,f, endpoint):
        self.parse(f)
        if len(self.extra):
            duration=3
        else:
            duration=3
        commands = [{
            'cmd': 'add',
            'args': {
                'type': 'text',
                'args': {
                    'text': {
                        'sender':self.sender,
                        'subject':self.subject,
                        'body':self.body
                    },
                    #'text_preprocessor': "display_email",
                    'speech_preprocessor': "pronounce_email",
                    'text2speech': "google",
                    'text2screen': "email",
                    #'renderer': "email",
                    'duration': duration,
                    #'speed': 1.5,
                }
            }
        }]
        commands += self.extra
        print send_mz_commands(endpoint, commands)


if __name__ == "__main__":
    if len(sys.argv)==2:
        queue=sys.argv[1]
    else:
        queue="http://musicazoo.mit.edu/queue"
    EmailParser().queue_email(sys.stdin, queue)
