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


