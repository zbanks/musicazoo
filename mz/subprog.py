import sys
import asyncio
import aiozmq
import zmq
import json
import subprocess
import traceback
from mz.util import *

class SubprogError(Exception):
    pass

class Subprog:
    CONNECT_TIMEOUT = 1
    UPDATE_TIMEOUT = 0.1

    def __init__(self, cmd_socket, update_socket):
        self.cmd_socket = cmd_socket
        self.update_socket = update_socket
        self.loop = asyncio.get_event_loop()

    async def update(self, data=None):
        self.update_stream.write((request(data),))
        f = self.update_stream.read()
        f = asyncio.wait_for(f, self.UPDATE_TIMEOUT)
        incoming_data_bytes = (await f)[0]
        return handle_reply(incoming_data_bytes)

    async def until_cmd(self):
        incoming_data_bytes = (await self.cmd_stream.read())[0]
        obj = handle_request(incoming_data_bytes)
        return obj

    def send_reply(self, *args, **kwargs):
        self.cmd_stream.write((reply(*args, **kwargs),))

    async def start(self):
        self.cmd_stream = None
        self.update_stream = None

        try:
            f = aiozmq.create_zmq_stream(
                zmq.REP,
                bind=self.cmd_socket)
            f = asyncio.wait_for(f, self.CONNECT_TIMEOUT)
            self.cmd_stream = await f 

            f = aiozmq.create_zmq_stream(
                zmq.REQ,
                connect=self.update_socket)
            f = asyncio.wait_for(f, self.CONNECT_TIMEOUT)
            self.update_stream = await f

            await self.update({"cmd": "init"})

            try:
                f = self.until_cmd()
                f = asyncio.wait_for(f, self.CONNECT_TIMEOUT)
                obj = await f
            except json.decoder.JSONDecodeError:
                self.send_reply(error="No valid JSON decoded")
                raise
            if not isinstance(obj, dict):
                self.send_reply(error="Root must be object")
                raise SubprogError("Root must be object")
            if "cmd" not in obj:
                self.send_reply(error='Root must contain "cmd"')
                raise SubprogError('Root must contain "cmd"')
            if obj["cmd"] != "init":
                self.send_reply(error='First "cmd" must be "init"')
                raise SubprogError('First "cmd" must be "init"')

            try:
                result = await self.init(obj)
            except Exception as e:
                self.send_reply(error=repr(e))
                raise
            self.send_reply(result)

            await self.run()

        finally:
            if self.cmd_stream is not None:
                self.cmd_stream.close()
            if self.update_stream is not None:
                self.update_stream.close()

    async def run(self):
        self.quit_signal = asyncio.Event()
        parent_terminated = False
        while True:
            f1 = asyncio.Task(self.until_cmd())
            f2 = asyncio.Task(self.quit_signal.wait())
            (done, pending) = await asyncio.wait((f1, f2), return_when=asyncio.FIRST_COMPLETED)
            if f1 not in done:
                f1.cancel()
                try:
                    await f1
                except asyncio.CancelledError:
                    pass
                break

            try:
                obj = f1.result()
            except json.decoder.JSONDecodeError:
                self.send_reply(error="No valid JSON decoded")
                continue
            if not isinstance(obj, dict):
                self.send_reply(error="Root must be object")
                continue
            if "cmd" not in obj:
                self.send_reply(error='Root must contain "cmd"')
                continue

            if obj["cmd"] == "rm":
                await self.rm()
                self.send_reply()
                if f2 not in done:
                    f2.cancel()
                    try:
                        await f2
                    except asyncio.CancelledError:
                        pass
                parent_terminated = True
                break


            try:
                method = getattr(self, "do_" + obj["cmd"])
            except AttributeError as e:
                self.send_reply(error='Command not recognized: "{}"'.format(obj["cmd"]))
                continue
            try:
                result = await method(obj)
            except Exception as e:
                self.send_reply(error=repr(e))
                traceback.print_exc()
            else:
                self.send_reply(result)

        if not parent_terminated:
            await self.update({"cmd": "rm"})

    def quit(self):
        self.quit_signal.set()

    async def rm(self):
        pass

class SubprogConnection:
    CONNECT_TIMEOUT = 1
    CMD_TIMEOUT = 0.1
    NATURAL_DEATH_TIMEOUT = 1
    SIGTERM_TIMEOUT = 1

    def __init__(self, command, update_callback_cr):
        self.loop = asyncio.get_event_loop()
        self.command = command
        self.update_callback_cr = update_callback_cr

    async def until_update(self):
        incoming_data_bytes = (await self.update_stream.read())[0]
        return handle_request(incoming_data_bytes)

    def send_reply(self, *args, **kwargs):
        self.update_stream.write((reply(*args, **kwargs),))

    async def cmd(self, obj):
        self.cmd_stream.write((request(obj),))
        f = self.cmd_stream.read()
        f = asyncio.wait_for(f, self.CMD_TIMEOUT)
        incoming_data_bytes = (await f)[0]
        return handle_reply(incoming_data_bytes)

    async def launch(self, args = None):
        self.cmd_socket = "tcp://127.0.0.1:3655"
        self.update_socket = "tcp://127.0.0.1:3656"

        f = aiozmq.create_zmq_stream(
            zmq.REP,
            bind=self.update_socket)
        f = asyncio.wait_for(f, self.CONNECT_TIMEOUT)
        self.update_stream = await f

        self.p = subprocess.Popen(self.command + [self.cmd_socket, self.update_socket])

        try:
            try:
                f = self.until_update()
                f = asyncio.wait_for(f, self.CONNECT_TIMEOUT)
                obj = await f
            except json.decoder.JSONDecodeError:
                self.send_reply(error="No valid JSON decoded")
                raise
            if not isinstance(obj, dict):
                self.send_reply(error="Root must be object")
                raise SubprogError("Root must be object")
            if "cmd" not in obj:
                self.send_reply(error='Root must contain "cmd"')
                raise SubprogError('Root must contain "cmd"')
            if obj["cmd"] != "init":
                self.send_reply(error='First update "cmd" must be "init"')
                raise SubprogError('First update "cmd" must be "init"')
            self.send_reply()

            f = aiozmq.create_zmq_stream(
                zmq.REQ,
                connect=self.cmd_socket)
            f = asyncio.wait_for(f, self.CONNECT_TIMEOUT)
            self.cmd_stream = await f

            if args is None:
                args = {}
            args["cmd"] = "init"
            await self.cmd(args)

            await self.run()
        finally:
            await self.ensure_death()

    async def run(self):
        self.quit_signal = asyncio.Event()
        self_terminated = False
        while True:
            f1 = asyncio.Task(self.until_update())
            f2 = asyncio.Task(self.quit_signal.wait())
            (done, pending) = await asyncio.wait((f1, f2), return_when=asyncio.FIRST_COMPLETED)
            if f1 not in done:
                f1.cancel()
                try:
                    await f1
                except asyncio.CancelledError:
                    pass
                break

            try:
                obj = f1.result()
            except json.decoder.JSONDecodeError:
                self.send_reply(error="No valid JSON decoded")
                continue
            if not isinstance(obj, dict):
                self.send_reply(error="Root must be object")
                continue
            if "cmd" not in obj:
                self.send_reply(error='Root must contain "cmd"')
                continue

            if obj["cmd"] == "rm":
                self.send_reply()
                if f2 not in done:
                    f2.cancel()
                    try:
                        await f2
                    except asyncio.CancelledError:
                        pass
                self_terminated = True
                break

            try:
                result = await self.update_callback_cr(obj)
            except Exception as e:
                self.send_reply(error=repr(e))
                traceback.print_exc()
            else:
                self.send_reply(await self.update_callback_cr(obj))

        if not self_terminated:
            await self.cmd({"cmd": "rm"})

    def quit(self):
        self.quit_signal.set()

    async def ensure_death(self):
        try:
            await asyncio.wait_for(self.until_dead(), self.NATURAL_DEATH_TIMEOUT)
        except asyncio.TimeoutError:
            print("Subprog is not dead, sending SIGTERM...", file=sys.stderr)
            self.p.terminate()
            try:
                await asyncio.wait_for(self.until_dead(), self.SIGTERM_TIMEOUT)
            except asyncio.TimeoutError:
                print("Subprog is not dead, sending SIGKILL...", file=sys.stderr)
                self.p.kill()

    async def until_dead(self):
        while self.p.poll() is None:
            await asyncio.sleep(0.1)

def main(cls):
    if len(sys.argv) < 3:
        raise SubprogError("Expected at least two command line arguments, the command socket and the update socket")
    cmd_socket = sys.argv[-2]
    update_socket = sys.argv[-1]

    c = cls(cmd_socket, update_socket)
    asyncio.get_event_loop().run_until_complete(c.start())
