#!/usr/bin/env python

import mzbot
import sys

class MZVolumeBot(mzbot.MZBot):
    def get_vol_id(self):
        if self.static_capabilities is None:
            self.fetch_capabilities()
        for sc_id, sc in self.static_capabilities.items():
            if sc['class'] == 'volume':
                return sc_id
        else:
            raise Exception("No volume to set")

    def get_volume(self):
        vol_id = self.get_vol_id()
        res = self.assert_success(self.doCommands([
            {"cmd": "statics", "args": {
                "parameters": {
                    vol_id: ["vol"]
                }
            }
        }]))
        return res[0][vol_id]["vol"]

    def set_volume(self, v):
        vol_id = self.get_vol_id()
        res = self.assert_success(self.doCommands([
            {"cmd": "tell_static", "args": {
                "uid": vol_id,
                "cmd": "set_vol",
                "args": {"vol": v}
            }
        }]))

    def inc_volume(self, delta_v):
        MAX = 100
        MIN = 0
        vol = max(MIN, min(MAX, self.get_volume() + delta_v))
        self.set_volume(vol)


if __name__ == '__main__':
    mz = MZVolumeBot("http://musicazoo.mit.edu:9000/")
    if len(sys.argv) == 2:
        vol = int(sys.argv[1])
        mz.inc_volume(vol)
