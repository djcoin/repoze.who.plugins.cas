"""Test suite for repoze.who.plugins.cas"""

import unittest

from zope.interface.verify import verifyClass

from repoze.who.interfaces import IChallenger, IIdentifier, IAuthenticator
from zope.interface import implements

from repoze.who.plugins.cas.main_plugin import CASChallengePlugin as CCP

import urllib
import re

def get_ccp_fact(cas_url, remember_name):
    def ccp_factory(path_logout, path_toskip):
       regex_logout = [re.compile(a) for a in path_logout] 
       regex_toskip = [re.compile(a) for a in path_toskip] 
       return CCP(cas_url, regex_logout, regex_toskip,
           remember_name)
    return ccp_factory

# set by the setUp method
make_ccp = None


# fake rememberer object used by the CAS plugin
class rememberer_mock_none:
    implements(IIdentifier)
    #### IIdentifier ####
    def remember(self, environ, identity):
        return None

    #### IIdentifier ####
    def forget(self, environ, identity):
        return None

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, id(self))

#"""
#CHALLENGE
#=========

#* logout flag set : ensure:
#- we are forgetting, ie: wont have the repoze.who...id
#- we are redirected on some page

#* logout flag not set: ensure:
#/!\ - we were not already identified => wrong, if 401, request authen
#- we are forgetting
#- we are redirected on some page
#"""


class ChallengeTest(unittest.TestCase):
    
    def setUp(self):
        self.cas_url =  "http://whatever.cas.url"
        make_ccp = get_ccp_fact(self.cas_url,'remember')
        self.classic_ccp = make_ccp([],[])
        self.environ = {'wsgi.input':'',
	    'wsgi.url_scheme': 'http',
	    'SERVER_NAME': 'localhost',
	    'SERVER_PORT': '8080',
	    'CONTENT_TYPE':'text/html',
	    'CONTENT_LENGTH':0,
	    'REQUEST_METHOD':'POST',
            'SCRIPT_NAME':'',
	    'PATH_INFO': '/login',
	    'QUERY_STRING':'',
            'repoze.who.plugins':{'rememberer':rememberer_mock_none()},
            }

    def _check_headers(self):
        pass

    def test_implements(self):
        verifyClass(IChallenger, CCP, tentative=True)

#We just checked the location header:
#* login : redirection to cas_url (should the app_headers & forget checked?)
#* logout: redirection to cas_logout (check others headers?)
# TODO, testcases: 
# * different status may not change anything (yet, check this?)
# * check all headers (which should have been deleted/required etc.)      
    def test_login(self): 
        env = self.environ
        status = 401
        app_headers = forget_headers = []
        httpfound = self.classic_ccp.challenge(env,status,app_headers,forget_headers)

        self.assertEqual(httpfound.location().startswith(self.cas_url),True)
        #for h1,h2 in httpfound.headers
        #    self.assertEqual(httpfound.location.startswith(self.cas_url),True)

    def test_logout(self): 
        env = self.environ
        status = 401
        myurl = 'http://whatever.url'
        env['rwpc.logout'] = myurl
        app_headers = forget_headers = []
        # paste.httpexceptions
        httpfound = self.classic_ccp.challenge(env,status,app_headers,forget_headers)
        
        self.assertEqual(httpfound.location(), 
                         self.cas_url + 'logout?service=' + urllib.quote(myurl))


#"""
#IDENTIFY
#========
#Purpose: try to retrieve credentials
#
#test:
#if path_logout => return None
#if path_toskip => return None
#if ticket dans la request:
#    * if ticket valide => credentials
#    * else null
#if bhp => return None, the logout has already been processed, lets it hit the app 
#
#"""

from repoze.who.plugins.cas.tests import MyLayer
class IdentifyTest(unittest.TestCase):
    layer = MyLayer

    def setUp(self):
        cas_url = IdentifyTest.layer.server_url
        make_ccp = get_ccp_fact(cas_url,'remember')
        self.classic_ccp = make_ccp([".*logout.*"],[".*toskip.*"])
        self.environ = {'wsgi.input':'',
	    'wsgi.url_scheme': 'http',
	    'SERVER_NAME': 'localhost',
	    'SERVER_PORT': '8080',
	    'CONTENT_TYPE':'text/html',
	    'CONTENT_LENGTH':0,
	    'REQUEST_METHOD':'POST',
            'SCRIPT_NAME':'',
	    'PATH_INFO': '/login',
	    'QUERY_STRING':'',
            'repoze.who.plugins':{'rememberer':rememberer_mock_none()},
            }

    def test_implements(self):
        verifyClass(IIdentifier, CCP, tentative=True)


    def test_path(self): 
        env = self.environ.copy()
        env['PATH_INFO'] = "/logout"
        self.assertEqual(self.classic_ccp.identify(env),None)
        env['PATH_INFO'] = "/toskip"
        self.assertEqual(self.classic_ccp.identify(env),None)

# if a ticket is present 
    def test_ticket(self): 
        env = self.environ.copy()
        env['PATH_INFO'] = "/normal"
        env['QUERY_STRING'] = "ticket=valid" 
        self.assertEqual(self.classic_ccp.identify(env),{'login':'sim','password':''})
        
        env = self.environ.copy()
        env['PATH_INFO'] = "/normal"
        env['QUERY_STRING'] = "ticket=notvalid" 
        self.assertEqual(self.classic_ccp.identify(env),None)

    def test_while_logout(self):
        env = self.environ.copy()
# should short-circuit everything: its the CAS callback let's process
# the url normally now
        env['QUERY_STRING'] = "bhp=whatever" 
        self.assertEqual(self.classic_ccp.identify(env),None)

    def test_while_logout(self):
        env = self.environ.copy()
        env['PATH_INFO'] = "/logout"

        self.assertEqual(self.classic_ccp.identify(env),None)
# ensure it will be handled : ie=> the challenge_decider will call for a
# challenge 
        self.assertNotEqual(env.get('rwpc.logout'),None)

# TODO:
# should ensure by analyzing the environ that the request will be well handled
# we can't just check if it returned the good things, environ is moving too
# we got to define some method to see if the environ is well setup:
# identificates the different cases, associate a flag/method to retrieve them

# When there is nothing in the environ to check, 
# we should ensure nothing has changed

# provide to get/provide to set ? => for any cases

#TODO: 
# * To list of all flags used in the environ ?
#     => Better tests, better comprehension, implementations
# * Make stuffs more trivial to test: get_flag... ?



#AUTHENT
#=======
#Validate credentials returned by IDENTIFY:
#    problem, the authent has already been made by the CAS server

class AuthTest(unittest.TestCase):
   def setUp(self): 
       cas_url = None
       path_logout = None
       path_toskip = None
       remember_name = None
       self.ccp = CCP(cas_url, path_logout,
               path_toskip, remember_name)

        
   def test_auth(self):
# whatever they submit, authenticate is called, which implies login is set,
# validate
# /!\ IT MUST BE ONLY ONE identifier => the one really doing the authent
# TODO: had a variable in the environment specifying those credentials were
# retrieved by the CAS server and so already authenticated
       identity = {'login':'', 'pass':''}
       environ = {}
       self.assertNotEqual(self.ccp.authenticate(environ,identity),True)
        
        
   def test_implements(self):
       verifyClass(IAuthenticator, CCP, tentative=True)

