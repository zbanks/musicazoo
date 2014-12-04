import util

static_endpoints = {
    '/':'wsgi/static'
}

wsgi_endpoints = {
    '/queue':util.wsgi_control('localhost',5580),
    '/vol':util.wsgi_control('localhost',5581),
    '/supervisor':util.wsgi_control('localhost', 9001),
}
