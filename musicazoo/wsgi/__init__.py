import endpoints
import os
import werkzeug

not_found_app = werkzeug.exceptions.NotFound()

static_path = endpoints.static_endpoints["/"]

url_map = werkzeug.routing.Map([
    werkzeug.routing.Rule('/', endpoint='index.html'),
])

def application(environ, start_response):
    adapter = url_map.bind_to_environ(environ)
    try: 
        endpoint, values = adapter.match()
    except:
        return not_found_app(environ, start_response)
    else:
        file_path = os.path.join(static_path, endpoint)
        f = open(file_path)
        response = werkzeug.wrappers.Response(werkzeug.wsgi.wrap_file(environ, f), mimetype="text/html")
        return response(environ, start_response)


application = werkzeug.wsgi.SharedDataMiddleware(application, endpoints.static_endpoints)
application = werkzeug.wsgi.DispatcherMiddleware(application, endpoints.wsgi_endpoints)
