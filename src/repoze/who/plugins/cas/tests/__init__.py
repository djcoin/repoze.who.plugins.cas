from ConfigParser import ConfigParser
import os
import socket
import threading

import unittest
import doctest

from zope.testing import doctest
import paste.fixture
from paste.deploy import loadapp

import BaseHTTPServer
import random
import time
import errno

import urllib2

#########
# LAYER #
#########

# Layer providing  
class MyLayer:
#class MyBase(unittest.TestCase):
    server_url = None
    def setUp(self, *args, **kwargs):
        print "\n Calling the setup from MyLayer \n"
    
        self.teardowns = []

        def start_server():
            port, thread = _start_server()
            url = 'http://localhost:%s/' % port
            self.teardowns.append(lambda: stop_server(url, thread))
            return url

        MyLayer.server_url = start_server()
        #print "####### URL:" + MyLayer.server_url + "#######"


    def tearDown(self):
        print "\n Calling the tearDown from MyLayer \n"
        for f in self.teardowns:
            f()

    setUp = classmethod(setUp)
    tearDown = classmethod(tearDown)


####################
### SERVER STUFF ###
####################

class Server(BaseHTTPServer.HTTPServer):

    def __init__(self, *args):
        BaseHTTPServer.HTTPServer.__init__(self, *args)

    __run = True
    def serve_forever(self):
        while self.__run:
            self.handle_request()

    def handle_error(self, *_):
        print "Handling error on server"
        self.__run = False

from handler import Handler
def _run(port):
    server_address = ('localhost', port)
    httpd = Server(server_address, Handler)
    httpd.serve_forever()

# find a random port
def get_port():
    for i in range(10):
        port = random.randrange(20000, 30000)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            try:
                s.connect(('localhost', port))
            except socket.error:
                return port
        finally:
            s.close()
    raise RuntimeError, "Can't find port"

def _start_server():
    print "\n Starting the server... \n"
    port = get_port()
    thread = threading.Thread(target=_run, args=(port,))
    thread.setDaemon(True)
    thread.start()
    wait(port, up=True)
    return port, thread


def stop_server(url, thread=None):
    print "\n Stopping the server... \n"
    try:
        urllib2.urlopen(url+'__stop__')
    except Exception, e:
        pass
    if thread is not None:
        thread.join() 

def wait(port, up):
    addr = 'localhost', port
    for i in range(120):
        time.sleep(0.25)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(addr)
            s.close()
            if up:
                break
        except socket.error, e:
            if e[0] not in (errno.ECONNREFUSED, errno.ECONNRESET):
                raise
            s.close()
            if not up:
                break
    else:
        if up:
            raise
        else:
            raise SystemError("Couln't stop server")


