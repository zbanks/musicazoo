#!/usr/bin/env python

from musicazoo.lib.mzbot import MZBot
from musicazoo.lib.webserver import Webserver

import snaphax

import argparse
import json
import logging
import os
import re
import sys

HOST_NAME = ''
PORT_NUMBER=9009
MZQ_URL='http://musicazoo.mit.edu/cmd'

parser = argparse.ArgumentParser(description="Musicazoo bot to display snapchats.")
parser.add_argument("-f", "--config", type=open, required=False, help="Account configuration JSON file")
parser.add_argument("-u", "--username", type=str, required=False, help="Snapchat Username")
parser.add_argument("-p", "--password", type=str, required=False, help="Snapchat Password")
parser.add_argument("-o", "--output", type=str, required=False, help="Directory to store retrieved images")
parser.add_argument("-l", "--log", type=argparse.FileType("w"), default=sys.stdout, help="Directory to store retrieved images")

class SnapBot(MZBot, Webserver):
    def __init__(self, username, password, save_dir=None):
        Webserver.__init__(self, HOST_NAME, PORT_NUMBER)
        MZBot.__init__(self, MZQ_URL)

        self.sh = snaphax.Snaphax()
        self.username = username
        self.password = password
        self.save_dir = save_dir

    def html_transaction(self, form_data):
        if not form_data:
            return "Snapbot! Send snaps to '{}'!".format(self.username)
        if "refresh" in form_data:
            new_snaps = self.refresh()
            return "New snaps! ({})".format(new_snaps)
        if "snap" in form_data:
            #XXX zomg this is so bad - nginx should probably just handle this
            path = os.path.join(self.save_dir, form_data["snap"])
            snap_f = open(path)
            return snap_f

    def loop_forever(self, time=10.0):
        while True:
            self.refresh()
            os.sleep(time)

    def refresh(self):
        new_snaps = []
        snap_data = self.sh.login(self.username, self.password)
        if "snaps" in snap_data:
            for snap in snap_data["snaps"]:
                print "Snap: ", snap
                print "Media type:", self.sh.media[snap["m"]]
                print "Status:", self.sh.status[snap["st"]]
                print "Time (s):", snap.get("t", "(None)")
                print "Caption:", snap.get("cap_text", "(None)")

                if snap["m"] not in (self.sh.MEDIA_IMAGE, self.sh.MEDIA_VIDEO, self.sh.MEDIA_VIDEO_NOAUDIO):
                    print "Snap isn't media"
                    continue

                try:
                    media_blob = self.sh.fetch(snap["id"])
                except snaphax.SnaphaxException as ex:
                    print ex
                    continue
                filename = "{id}_{sn}".format(**snap)
                if self.save_dir:
                    with open(os.path.join(self.save_dir, filename), "wb") as f:
                        f.write(media_blob)
                        print "Wrote snap to ", f.name
                        new_snaps.append(filename)


if __name__ == "__main__":
    args = parser.parse_args()

    #TODO: Logging...

    if args.config:
        config_json = json.load(args.config)
        if all([x in config_json for x in ("username", "password", "output_directory")]):
            username = config_json["username"]
            password = config_json["password"]
            output_directory = config_json["output_directory"]
        else:
            print "Invalid configuration file"
            sys.exit()
    else:
        username = args.username
        password = args.password
        output_directory = args.output
        if any([not x for x in (username, password, output_directory)]):
            print "Supply -u, -p, and -o options or a configuration file"
            sys.exit()
        
    sb = SnapBot(username, password, output_directory)
#sb.refresh()
    sb.run()
