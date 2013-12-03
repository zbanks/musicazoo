# A simple bot framework

import requests
import json

class MZBot(object):
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.module_capabilities = None
        self.static_capabilities = None
        self.background_capabilities = None

    def doCommands(self, cmd_list):
        json_data = json.dumps(cmd_list)
        headers = {"Content-type": "text/json"}
        resp = requests.post(self.endpoint, data=json_data, headers=headers)
        return resp.json()

    def doCommand(self,cmd):
        return self.doCommands([cmd])[0]

    def fetch_capabilities(self):
        cap_resp = self.assert_success(self.doCommands([
            {"cmd":"module_capabilities"},
            {"cmd":"static_capabilities"},
            {"cmd":"background_capabilities"}
        ]))
        self.module_capabilities = cap_resp[0]
        self.static_capabilities = cap_resp[1]
        self.background_capabilities = cap_resp[2]

    def assert_success(self,result):
        if isinstance(result,dict):
            if result['success']:
                if 'result' in result:
                    return result['result']
                return None
            raise Exception(result['error'])
        
        if isinstance(result,list):
            for r in result:
                if not r['success']:
                    raise Exception(r['error'])
            return [r['result'] for r in result if 'result' in r]
        raise Exception('Bad response type from server')

if __name__=='__main__':
    import sys
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9000/"
    b = MZBot(endpoint)
    print b.doCommands([{'cmd':'static_capabilities'}])
