import json

class RemoteError(Exception): pass

def handle_reply(data):
    data = str(data, encoding="utf-8")
    obj = json.loads(data)

    assert "success" in obj
    if obj["success"]:
        if "result" in obj:
            return obj["result"]
    else:
        assert "error" in obj
        raise RemoteError(obj["error"])

def reply(result = None, error = None):
    if error:
        obj = {"success": False, "error": error}
    else:
        obj = {"success": True}
        if result is not None:
            obj["result"] = result
    data = json.dumps(obj)
    data = bytes(data, encoding="utf-8")
    return data

def handle_request(data):
    data = str(data, encoding="utf-8")
    obj = json.loads(data)
    return obj

def request(obj = None):
    data = json.dumps(obj)
    data = bytes(data, encoding="utf-8")
    return data
