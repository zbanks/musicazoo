#!/usr/bin/env python

import asyncio
import aiozmq
import zmq
import subprocess
from mz.subprog import SubprogConnection
from mz.util import *

async def update_cr(args):
    print(args)

s = SubprogConnection(["python", "-m", "mz.bin.youtube", "settings/youtube.json"], update_cr)

async def go():
    await s.launch({"url": "https://www.youtube.com/watch?v=F57P9C4SAW4"})

asyncio.get_event_loop().run_until_complete(go())
