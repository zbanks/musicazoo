# Python library that implements a subset of the Snapchat API
#
# (c) Copyright 2012 Zach Banks <zbanks@mit.edu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import requests
import hashlib
from Crypto.Cipher import AES

class SnaphaxException(Exception):
    pass

class SnaphaxAuthException(SnaphaxException):
    pass

class Snaphax(object):
    DEFAULT_OPTIONS = {
		'blob_enc_key' : 'M02cnQ51Ji97vwT4',
		'debug' : False,
		'pattern' : '0001110111101110001111010101111011010001001110011000110001000110',
		'secret' : 'iEk21fuwZApXlz93750dmW22pw389dPwOk',
		'static_token' : 'm198sOkJEn37DjqZ32lpRu76xmw288xSQ9',
		'url' : 'https://feelinsonice.appspot.com',
		'user_agent' : 'Snaphax 4.0.1 (iPad; iPhone OS 6.0; en_US)',
        'username' : ''
    }
    STATUS_NONE = -1
    STATUS_SENT = 0
    STATUS_NEW = 1
    STATUS_VIEWED = 2
    STATUS_SCREENSHOT = 3

    MEDIA_IMAGE = 0
    MEDIA_VIDEO = 1
    MEDIA_VIDEO_NOAUDIO = 2
    FRIEND_REQ = 3
    FRIEND_REQ_IMAGE = 4
    FRIEND_REQ_VIDEO = 5
    FRIEND_REQ_VIDEO_NOAUDIO = 6

    PORTRAIT = 0
    LANDSCAPE_LEFT = 1
    LANDSCAPE_RIGHT = 2

    FRIEND = 0
    FRIEND_PENDING = 1
    FRIEND_BLOCKED = 2

    status = {STATUS_NONE: "(none)",
              STATUS_SENT: "Sent",
              STATUS_NEW: "New",
              STATUS_VIEWED: "Viewed",
              STATUS_SCREENSHOT: "Screenshot" }

    media = {MEDIA_IMAGE: "Image",
             MEDIA_VIDEO: "Video (audio)",
             MEDIA_VIDEO_NOAUDIO: "Video (no audio)",
             FRIEND_REQ: "Friend Request",
             FRIEND_REQ_IMAGE: "Friend Request (Image)",
             FRIEND_REQ_VIDEO: "Friend Request (Video + audio)",
             FRIEND_REQ_VIDEO_NOAUDIO: "Friend Request (Video, no audio)" }

    orientation = {PORTRAIT: "Portrait",
                   LANDSCAPE_LEFT: "Landscape (left)",
                   LANDSCAPE_RIGHT: "Landscape (right)" }

    friend = {FRIEND: "Friend",
              FRIEND_PENDING: "Pending",
              FRIEND_BLOCKED: "Blocked" }

    def __init__(self, debug=True, **kwargs):
        self.options = self.DEFAULT_OPTIONS.copy()
        self.options.update(kwargs)
        self.auth_token = None
        self.logger = None
        self.debug = debug

    def login(self, username, password):
        ts = self._time()
        self.options["username"] = username
        post_data = {"username": username,
                     "password": password,
                     "timestamp": ts }
        out = self.post("/ph/login", post_data, self.options["static_token"], ts);
        try:
            json = out.json()
        except requests.JSONDecodeError:
            raise SnaphaxException("Unable to login; JSONDecodeError")
        self.auth_token = json["auth_token"]
        return json

    def fetch(self, bid):
        if not self.auth_token:
            raise SnaphaxAuthException("Unable to fetch image; not logged in")
        ts = self._time()
        post_data = {"id": bid,
                     "timestamp": ts,
                     "username": self.options["username"] }
        res = self.post("/ph/blob", post_data, self.auth_token, ts)
        raw = res.raw.data
        if self._is_html(raw):
            raise SnaphaxException("Unable to fetch image; recieved HTML response: \n" + raw)
        if self._is_valid_header(raw):
            return raw
        decoded = self._decrypt(raw)
        self._log(hex_header=[hex(ord(t)) for t in decoded[0:2]])
        if self._is_valid_header(decoded):
            return decoded
        else:
            raise SnaphaxException("Unable to fetch image; unable to decode format")

        return res
    def upload(self, file_data, file_type, recipients, time=3):
        if file_type not in (self.MEDIA_IMAGE, self.MEDIA_VIDEO, self.MEDIA_VIDEO_NOAUDIO):
            raise SnaphaxException("Unable to upload; media type %d not defined" % file_type)
        if not self.auth_token:
            raise SnaphaxAuthException("Unable to upload; not logged in")
        ts = self._time()
        media_id = self.options["username"].upper() + str(ts)
        enc_file_data = self._encrypt(file_data)
        files = {"data": ("file", enc_file_data)}
        data = {"username": self.options["username"],
                "timestamp": ts,
                "type": file_type,
                "media_id": media_id }
        res = self.post("/ph/upload", data, self.auth_token, ts, files=files)
        self._log(http_response=res, http_response_data=res.raw.data)
        if not res:
            raise SnaphaxException("Unable to upload; /ph/upload returned error")

        ts = self._time()
        rdata = {"username": self.options["username"],
                 "timestamp": ts,
                 "recipient": ", ".join(recipients),
                 "media_id": media_id,
                 "time": time }
        rres = self.post("/ph/send", rdata, self.auth_token, ts)
        self._log("Sent to %s" % recipients)
        self._log(http_response=rres, http_response_data=rres.raw.data)
        if not rres:
            raise SnaphaxException("Unable to upload; /ph/send returned error")

    def post(self, endpoint, data, token, ts, files=None):
        headers = {"User-Agent": self.options["user_agent"] }
        url = self.options["url"] + endpoint
        token = self._hash(token, ts)
        data["req_token"] = token
        r = requests.post(url, data=data, headers=headers, stream=True, files=files)
        return r
    def _time(self):
        return str(int(time.time() * 1000))
    def _hash(self, p1, p2):
        sha256 = lambda x: hashlib.sha256(x).hexdigest()
        s1 = self.options["secret"] + p1
        s2 = p2 + self.options["secret"]
        s3 = sha256(s1)
        s4 = sha256(s2)
        out = "".join(map(lambda x, a, b: a if x == '0' else b, self.options["pattern"], s3, s4))
        return out
    def _is_valid_header(self, header):
        return header[0:2] in (chr(0)+chr(0), chr(0xff)+chr(0xd8))
    def _is_html(self, header):
        return header[0:2] == "<h"
    def _decrypt(self, data):
        enc = AES.new(self.options["blob_enc_key"], AES.MODE_ECB)
        return enc.decrypt(data)
    def _encrypt(self, data):
        enc = AES.new(self.options["blob_enc_key"], AES.MODE_ECB)
        return enc.encrypt(data)
    
    def _log(self, *args, **kwargs):
        log_str = " ".join(map(str, args))
        if kwargs:
            log_str += "\n" + "\n".join(["%s: %s" % i for i in kwargs.items()])
        if self.debug:
            print log_str
        if self.logger:
            logger.info(log_str)



