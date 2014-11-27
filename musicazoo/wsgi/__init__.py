import werkzeug
import endpoints

application = werkzeug.exceptions.NotFound()
application = werkzeug.wsgi.SharedDataMiddleware(application, endpoints.static_endpoints)
application = werkzeug.wsgi.DispatcherMiddleware(application, endpoints.wsgi_endpoints)
