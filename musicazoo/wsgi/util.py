import werkzeug
import json
import socket

def wsgi_control(addr,port,timeout=10):

    def query(inp):
        data=json.dumps(inp)
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
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
        mimetype, options = werkzeug.http.parse_options_header(request.content_type)
        if mimetype == 'text/json':
            inp=json.loads(request.data.decode(options.get('charset', 'utf-8')))
            try:
                outp=query(inp)
            except Exception as e:
                return werkzeug.exceptions.InternalServerError(e)
            return werkzeug.Response(json.dumps(outp),content_type='text/json')
        return werkzeug.Response('Endpoint only accepts JSON.')
    return wsgi
