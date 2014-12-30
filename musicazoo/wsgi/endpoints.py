import util
import pkg_resources

static_endpoints = {
    '/': pkg_resources.resource_filename("musicazoo.wsgi", '../../static')
    #'/': ("musicazoo.wsgi", "../../static")
}

wsgi_endpoints = {
    '/queue':util.wsgi_control('localhost',5580),
    '/vol':util.wsgi_control('localhost',5581),
    '/nlp':util.wsgi_control('localhost',5582),
    '/top':util.wsgi_control('localhost',5583),
    '/lux':util.wsgi_control('localhost',5584),
    #'/supervisor':util.wsgi_control('localhost', 9001),
}
