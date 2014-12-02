import werkzeug
import json
import socket

def wsgi_control(addr,port):
    timeout=10000

    def zmq_query(inp):
        data=json.dumps(inp)
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((addr,port))
        s.sendall(data+'\n')
        result=''
        while True:
            result+=s.recv(4096)
            if '\n' in result:
                result=result[0:result.find('\n')]
                break
        s.close()
        return json.loads(result)

    @werkzeug.Request.application
    def wsgi(request):
        if request.headers.get('content-type') == 'text/json':
            inp=json.loads(request.data)
            try:
                outp=zmq_query(inp)
            except Exception as e:
                return werkzeug.exceptions.InternalServerError(e)
            return werkzeug.Response(json.dumps(outp),content_type='text/json')
        return werkzeug.Response('Endpoint only accepts JSON.')
    return wsgi
