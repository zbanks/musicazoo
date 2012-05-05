#!/usr/bin/python

import logging
import asyncore
import socket
import json


logging.basicConfig(level=logging.DEBUG, format="%(created)-15s %(msecs)d %(levelname)8s %(thread)d %(name)s %(message)s")
log                        = logging.getLogger(__name__)

BACKLOG                    = 5
SIZE                    = 1024

class Handler(asyncore.dispatcher):

    def __init__(self, conn_sock, client_address, server):
        self.server                = server
        self.client_address        = client_address
        self.recv_buffer             = ""
        self.send_buffer             = ""

        # We dont have anything to write, to start with
        self.is_writable        = False
        self.is_readable    = True

        # Create ourselves, but with an already provided socket
        asyncore.dispatcher.__init__(self, conn_sock)
        log.debug("created handler; waiting for loop")

    def readable(self):
        return self.is_readable        # We are always happy to read

    def writable(self):
        return self.is_writable # But we might not have
                                # anything to send all the time

    def handle_read(self):
#log.debug("handle_read")
        data = self.recv(SIZE)
#log.debug("after recv")
        if data:
#log.debug("got data")
            self.recv_buffer += data
            line=self.readline()
            if line!=None:
                self.got_data(line)
        else:
            log.debug("got null data")

    def handle_write(self):
#log.debug("handle_write")
        if self.send_buffer:
            sent = self.send(self.send_buffer)
#log.debug("sent data")
            self.send_buffer = self.send_buffer[sent:]
        else:
            log.debug("nothing to send")
        if len(self.send_buffer) == 0:
            self.is_writable = False

    # Will this ever get called?  Does loop() call
    # handle_close() if we called close, to start with?
    def handle_close(self):
#       log.debug("handle_close")
        log.info("conn_closed: client_address=%s:%s" % \
                     (self.client_address[0],
                      self.client_address[1]))
        self.close()
        #pass

    def readline(self):
        newline=self.recv_buffer.find('\n')
        if newline<0:
            return None
        out=self.recv_buffer[:newline]
        self.recv_buffer=self.recv_buffer[newline+1:]
        return out

    def got_data(self,line):
        """
        Process incoming data from socket

        Recieves one line from buffer.
        The line is attempted to be parsed as JSON,
        then passed to the dispatcher
        """
        log.debug("got line: line=%s" % (line))
        line_len=len(line)
        try:
            json_data = json.loads(line)
            if not json_data:
                self.error()
            else:
                response = self.server.dispatch.from_data(json_data)
                self.socketprint(json.dumps(response))
        except ValueError:
            self.error()
    
    def error(self):
        self.socketprint("{ 'success': false, 'error': \"Unable to parse JSON\" }")

    def ok(self):
        self.socketprint("{ 'success': true,  error: null }")

    def socketprint(self,message):
        self.send_buffer+=message+"\n"
        self.is_writable=True

class Server(asyncore.dispatcher):

    allow_reuse_address            = False
    request_queue_size            = 5
    address_family                = socket.AF_INET
    socket_type                    = socket.SOCK_STREAM

    def __init__(self, address, dispatcher):
        self.handlerClass        = Handler

        self.address            = address
        self.dispatch        = dispatcher

        asyncore.dispatcher.__init__(self)
        self.create_socket(self.address_family,
                               self.socket_type)

        if self.allow_reuse_address:
            self.set_resue_addr()

        self.server_bind()
        self.server_activate()

    def server_bind(self):
        self.bind(self.address)
        log.debug("bind: address=%s:%s" % (self.address[0], self.address[1]))

    def server_activate(self):
        self.listen(self.request_queue_size)
        log.debug("listen: backlog=%d" % self.request_queue_size)

    def fileno(self):
        return self.socket.fileno()

    def serve_forever(self):
        asyncore.loop()

    # TODO: try to implement handle_request()

    # Internal use
    def handle_accept(self):
        (conn_sock, client_address) = self.accept()
        if self.verify_request(conn_sock, client_address):
            self.process_request(conn_sock, client_address)

    def verify_request(self, conn_sock, client_address):
        return True

    def process_request(self, conn_sock, client_address):
        log.info("conn_made: client_address=%s:%s" % \
                     (client_address[0],
                      client_address[1]))
        self.handlerClass(conn_sock, client_address, self)

    def handle_close(self):
        self.close()

