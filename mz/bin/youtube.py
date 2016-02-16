#!/usr/bin/env python

import asyncio

import mz.subprog
import mz.settings

import subprocess
import os
import tempfile
import fcntl

class Youtube(mz.subprog.Subprog):
    BUF_SIZE = 4 * 1024 * 1024
    VLC_STARTUP_TIME = 0.1
    VLC_TIMEOUT = 0.1

    async def init(self, args):
        self.rc_host = settings["vlc_rc_host"]
        self.rc_port = 5666
        self.url = args["url"]
        self.youtube_dl = subprocess.Popen(settings["youtube-dl"] + [self.url], stdout=subprocess.PIPE)
        self.vlc = subprocess.Popen(settings["vlc"] + ["--rc-host", "{}:{}".format(self.rc_host, self.rc_port)], stdin=subprocess.PIPE)

        self.buf = b""

        fl = fcntl.fcntl(self.youtube_dl.stdout.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(self.youtube_dl.stdout.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
        fl = fcntl.fcntl(self.vlc.stdin.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(self.vlc.stdin.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.loop.add_reader(self.youtube_dl.stdout.fileno(), self.read_youtube_dl)
        self.writer_is_active = False
        self.reader_is_active = True
        self.pipe_over = False

        self.loop.create_task(self.task())

    def read_youtube_dl(self):
        chunksize = 1024 * 16
        first = True
        while True:
            try:
                read = os.read(self.youtube_dl.stdout.fileno(), chunksize)
            except OSError as e:
                if e.errno == 11:
                    return
                else:
                    raise

            if len(read) == 0 and first:
                self.pipe_over = True
                self.loop.remove_reader(self.youtube_dl.stdout.fileno())
                return
            first = False
            self.buf += read
            if len(self.buf) > 0 and not self.writer_is_active:
                self.loop.add_writer(self.vlc.stdin.fileno(), self.write_vlc)
                self.writer_is_active = True
            if len(self.buf) >= self.BUF_SIZE:
                self.loop.remove_reader(self.youtube_dl.stdout.fileno())
                self.reader_is_active = False
                return
            if len(read) < chunksize:
                return

    def write_vlc(self):
        chunksize = 1024 * 16
        while True:
            if len(self.buf) == 0:
                if self.pipe_over:
                    os.close(self.vlc.stdin.fileno())
                self.loop.remove_writer(self.vlc.stdin.fileno())
                self.writer_is_active = False
                return

            to_write = min(chunksize, len(self.buf))
            try:
                l = os.write(self.vlc.stdin.fileno(), self.buf[0:to_write])
            except OSError as e:
                if e.errno == 11:
                    return
                elif e.errno == 32:
                    self.loop.remove_writer(self.vlc.stdin.fileno())
                    return
                else:
                    raise
            self.buf = self.buf[l:]
            if len(self.buf) < self.BUF_SIZE and self.reader_is_active == False:
                self.loop.add_reader(self.youtube_dl.stdout.fileno(), self.read_youtube_dl)
                self.reader_is_active = True
            if l < to_write:
                return

    async def rm(self):
        self.loop.remove_reader(self.youtube_dl.stdout.fileno())
        self.loop.remove_writer(self.vlc.stdin.fileno())

        if self.vlc.poll() is None:
            self.vlc.terminate()
        if self.youtube_dl.poll() is None:
            self.youtube_dl.terminate()
        for i in range(5):
            if self.vlc.poll() is not None and self.youtube_dl.poll() is not None:
                break
            await asyncio.sleep(0.1)
        if self.vlc.poll() is None:
            self.vlc.kill()
        if self.youtube_dl.poll() is None:
            self.youtube_dl.kill()

    async def rc_cmd(self, cmd, response=False):
        self.writer.write(cmd + b"\n")
        await asyncio.wait_for(self.writer.drain(), self.VLC_TIMEOUT)
        if response:
            line = await asyncio.wait_for(self.reader.readline(), self.VLC_TIMEOUT)
            while line[0:2] == b'> ':
                line = line[2:]
            return line.strip()

    async def pause(self):
        if not self.paused and not self.hidden:
            await self.rc_cmd(b"pause")
        self.paused = True

    async def play(self):
        if self.paused and not self.hidden:
            await self.rc_cmd(b"play")
        self.paused = False

    async def get_time(self):
        result = await self.rc_cmd(b"get_time", True)
        if result == b'':
            return None
        return int(result)

    async def hide(self):
        if self.hidden:
            return
        if not self.paused:
            await self.rc_cmd(b"pause")
        await self.rc_cmd(b"vtrack -1")
        self.hidden = True

    async def show(self):
        if not self.hidden:
            return
        await self.rc_cmd(b"vtrack 0")
        if not self.paused:
            await self.rc_cmd(b"play")
        self.hidden = False

    async def task(self):
        try:
            await asyncio.sleep(self.VLC_STARTUP_TIME)
            (self.reader, self.writer) = await asyncio.open_connection(self.rc_host, self.rc_port)
            banner = await asyncio.wait_for(self.reader.readline(), self.VLC_TIMEOUT)
            help_line = await asyncio.wait_for(self.reader.readline(), self.VLC_TIMEOUT)
            assert banner.startswith(b"VLC")
            assert help_line.startswith(b"Command")

            self.paused = False
            self.hidden = True

            while self.vlc.poll() is None:
                print(await self.get_time())
                await asyncio.sleep(0.1)

        finally:
            await self.rm()
            self.quit()

if __name__ == "__main__":
    settings = mz.settings.load_from_arg()
    mz.subprog.main(Youtube)
