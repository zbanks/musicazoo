#!/usr/bin/python

from musicazoo.lib.mzbot import MZBot
from usbutton import USButton

import time
import sqlite3
import os
import re

class TrackerBot(MZBot):
    def __init__(self,url):
        self.uid = None
        self.btn = USButton('/dev/input/by-id/usb-Eric_USB_Button-event-if00')
        self.btn.callback = lambda x: self.btn_press(x)
        MZBot.__init__(self,url)

    def poll_mz(self):
        req={'cmd':'cur','args':{}}
        result=self.assert_success(self.doCommand(req))
        if result:
            self.uid = result['uid']
            self.btn.led = True
        else:
            self.uid = None
            self.btn.led = False

    def btn_press(self, x):
        if self.uid is not None and x:
            self.assert_success(self.doCommand(
                    {'cmd':'tell_module','args':{'uid':self.uid,'cmd':'stop'}}
            ))

if __name__ == "__main__":
    tb = TrackerBot("http://musicazoo.mit.edu/cmd")
    while True:
        tb.poll_mz()
        time.sleep(1)
