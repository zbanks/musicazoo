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

    async def init(self, args):
        self.url = args["url"]
        self.youtube_dl = subprocess.Popen(settings["youtube-dl"] + ["-o-", self.url], stdout=subprocess.PIPE)
        self.vlc = subprocess.Popen(settings["vlc"], stdin=subprocess.PIPE)

        self.buf = b''

        fl = fcntl.fcntl(self.youtube_dl.stdout.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(self.youtube_dl.stdout.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
        fl = fcntl.fcntl(self.vlc.stdin.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(self.vlc.stdin.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.loop.add_reader(self.youtube_dl.stdout.fileno(), self.read_youtube_dl)
        self.writer_is_active = False
        self.reader_is_active = True

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

            if len(read) == 0 and first:
                print("input over")
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
                self.loop.remove_writer(self.vlc.stdin.fileno())
                self.writer_is_active = False
                return

            to_write = min(chunksize, len(self.buf))
            try:
                l = os.write(self.vlc.stdin.fileno(), self.buf[0:to_write])
            except OSError as e:
                if e.errno == 11:
                    return
                if e.errno == 32:
                    print("output over")
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
        os.unlink(self.fifo_fn)
        os.rmdir(self.fifo_dir)
        self.vlc.terminate()
        self.youtube_dl.terminate()

    async def task(self):
        print("Twiddling thumbs...")

if __name__ == "__main__":
    settings = mz.settings.load_from_arg()
    mz.subprog.main(Youtube)
