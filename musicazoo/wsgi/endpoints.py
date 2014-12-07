import util

static_endpoints = {
    '/':'static'
}

wsgi_endpoints = {
    '/queue':util.wsgi_control('localhost',5580),
    '/vol':util.wsgi_control('localhost',5581),
    '/nlp':util.wsgi_control('localhost',5582),
    '/supervisor':util.wsgi_control('localhost', 9001),
}
