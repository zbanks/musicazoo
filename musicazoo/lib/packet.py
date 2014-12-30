import hashlib
import hmac
import json

def error(err):
    return {'success':False,'error':err}

def good(payload=None):
    if payload is not None:
        return {'success':True,'result':payload}
    return {'success':True}

def assert_success(response):
    if not isinstance(response,dict) or 'success' not in response:
        print "E",response
        raise Exception("Malformed response")
    if 'success' not in response:
        raise Exception("Malformed response")
    if response['success']:
        if 'result' in response:
            return response['result']
        return
    if 'error' not in response:
        raise Exception("Malformed response")
    raise Exception(response['error'])


# Signed commands
# How do we prevent replay attacks? 
def parse(msg, key=None):
    if msg[0] == "$":
        remote_signature = msg[1:65]
        msg = msg[65:]
    else:
        remote_signature = None

    if key is not None:
        h = hmac.new(key, msg, hashlib.sha256)
        local_signature = h.hexdigest()
        if local_signature != remote_signature:
            # Signature mismatch
            raise Exception("Invalid signature")

    data = json.parse(msg)

    return data

def serialize(msg, key=None):
    text_msg = json.dumps(msg)
    if key is not None:
        signature = hmac.new(key, text_msg, hashlib.sha256).hexdigest()
        text_msg = "${}{}".format(signature, text_msg)
    return text_msg



