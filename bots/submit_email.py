#!/usr/bin/env python
import email
import json
import os
import re
import requests
import sys

class EmailParser:
    def __init__(self,f=None):
        if f==None:
            return
        msg = email.message_from_file(f)
        self.extra = []
        self.sender = msg["From"]
        self.text="From: {0}\n".format(msg["From"])
#self.speech="Email from {0}.\n".format(self.translate_from(msg["From"]))
        self.text+="Subject: {0}\n".format(msg["Subject"])
#self.speech+="Subject. {0}.\n".format(self.translate(msg["Subject"]))
        
#if "voice.google.com" in msg["from"] and "SMS" in msg["Subject"]:
#pass    
         
        for part in msg.walk():
            if part.is_multipart():
                continue
            if part.get_content_type() == "text/plain":
                msg=self.strip_reply(part.get_payload())
                self.text+=msg
#self.speech+=self.translate(msg)
                self.find_extra(msg)

    def find_extra(self,msg):
        ytm=re.findall("youtube\.com\/watch\?v=([^& ]+)",msg)
        for yt in ytm:
           self.extra.append(["http://youtube.com/watch?v="+yt])
        if len(self.extra)>3:
            self.extra=self.extra[0:3]

    def translate_from(self,fromaddr):
        complex_addr_match=re.search("^([^<]*?)\\s*<([^@]+)@([^>]+)>$",fromaddr)
        if complex_addr_match==None:
            addr_match=re.search("^([^@]+)@(.+)$",fromaddr)
            if addr_match==None:
                return fromaddr
            (uname,domain)=addr_match.group(1,2)
            canonical=None
        else:
            (canonical,uname,domain)=complex_addr_match.group(1,2,3)
            if len(canonical)==0:
                canonical=None
        if domain.lower()=="mit.edu":
            fingered=finger(uname)
            if fingered!=None:
                return fingered
        if canonical!=None:
            return canonical
        return "{0} at {1}".format(uname,domain)

    # Email-specific replaces
    def translate(self,rawtxt):
        """
        replaces = (
                (r"Re:", "Reply to "),
                (r"reuse", "re-use"),
                (r"<?(http:\/\/)?([a-zA-Z0-9\-.]+\.[a-zA-Z0-9\-]+([\/]([a-zA-Z0-9_\/\-.?&%=\(\)+])*)*)>?", r".link."),
        )
        for ptrn, repl in replaces:
            rawtxt = re.sub(ptrn, repl, rawtxt)
        """
        return rawtxt

    def strip_reply(self,msgtxt):
        delims = (r"-- ?\n",
                  r"-----Original Message-----",
                  r"________________________________",
                  r"\nOn [^\n]+ wrote:\n",
                  r"Sent from my iPhone",
                  r"sent from my BlackBerry",
                  r"\n>")
        for dlm in delims:
            msgtxt = re.split(dlm, msgtxt, 1)[0]
        return msgtxt


def finger(username):
	finger="/usr/bin/finger"
	p=subprocess.Popen([finger,username],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	(out,err)=p.communicate()
	matches=re.search("Name:\s+(.+)\n",out)
	if matches==None:
		return None
	return matches.group(1)

def queue_email(email_fn, queue="http://musicazoo.mit.edu/cmd"):
    with open(email_fn) as email_f:
        ep = EmailParser(email_f)
    email_text = ep.text
    extras = ep.extra
    sender = ep.sender
    commands = [{
        'cmd': 'add',
        'args': {
            'type': 'text',
            'args': {
                'text': email_text,
                'text_preprocessor': "email",
                'speech_preprocessor': "email",
                'text2speech': "google",
                'renderer': "email",
                'duration': 20,
                'speed': 1,
                'short_description': "Email from {}".format(sender),
                'long_description': "Email from {}".format(sender),
            }
        }
    }]
    for extra in extras:
        commands.append({
           'cmd': 'add',
           'args': {
               'type': 'youtube',
               'args': { 'url': extra }
            }
        })
    print requests.post(queue, json.dumps(commands)).text

if __name__ == "__main__":
    queue_email(sys.argv[1], queue="http://192.168.0.10/cmd")
import subprocess
import re
