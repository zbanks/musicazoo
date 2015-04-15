import util
import pkg_resources
import musicazoo.settings as settings

static_endpoints = {
    #'/': pkg_resources.resource_filename("musicazoo.wsgi", '../../static')
    #'/': ("musicazoo.wsgi", "../../static")
    '/': settings.static_path
}

wsgi_endpoints = {
    '/queue':util.wsgi_control('localhost', settings.ports["queue"]),
    '/vol':util.wsgi_control('localhost', settings.ports["vol"]),
    '/nlp':util.wsgi_control('localhost', settings.ports["nlp"]),
    '/top':util.wsgi_control('localhost', settings.ports["top"]),
    '/lux':util.wsgi_control('localhost', settings.ports["lux"]),
    #'/supervisor':util.wsgi_control('localhost', 9001),
}
