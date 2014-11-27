import util

static_endpoints = {
    '/':'static'
}

wsgi_endpoints = {
    '/cmd':util.wsgi_control('localhost',5580)
}
