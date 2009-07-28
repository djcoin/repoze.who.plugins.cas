"""Test suite for repoze.who.plugins.cas"""

from zope.interface.verify import verifyClass
from repoze.who.interfaces import IChallenger, IIdentifier, IAuthenticator
from repoze.who.plugins.cas.challenge_decider import my_challenge_decider 

import unittest
import re

class ChallengeDeciderTest(unittest.TestCase):

    cd = my_challenge_decider

    def setUp(self):
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
            }
       path_login = [
                '.*login$',
                ]
       self.regex_login = [re.compile(a) for a in path_login] 



    def test_cd_logmatch(self):
# flag meaning the user is authent
        environ = self.environ.copy()
        my_cd = self.cd(self.regex_login)
# need to authent : path_info should match the regex
        self.assertEqual(my_cd(environ,'200 Ok',{}),True)

        environ = self.environ.copy()
        environ.update({'repoze.who.identity':''})
        self.assertEqual(my_cd(environ,'401 Unauthorized',{}),True)

        environ = self.environ.copy()
        environ.update({'repoze.who.identity':''})
        self.assertEqual(my_cd(environ,'200 Ok',{}),False)

    def test_cd_logdontmatch(self):
        env = self.environ.copy()
        env['PATH_INFO'] = '/whatever' # won't trigger the loggin process

        cd_list = [self.cd(self.regex_login),
                   self.cd(),]

        
        for my_cd in cd_list:
            environ = env.copy()
            self.assertEqual(my_cd(environ,'200 Ok',{}),False)

            environ = env.copy()
            environ.update({'repoze.who.identity':''})
            self.assertEqual(my_cd(environ,'401 Unauthorized',{}),True)

            environ = env.copy()
            environ.update({'repoze.who.identity':''})
            self.assertEqual(my_cd(environ,'200 Ok',{}),False)


    def test_logged_out(self):
# flag meaning the user requested for a logout
# the challenge is triggered with the aim to trigger some action 
# to logout later...
        my_cd = self.cd(self.regex_login)
        environ = self.environ.copy()
        environ.update({'rwpc.logout':''})

#whatever header: logout
        self.assertEqual(my_cd(environ,'401 Unauthorized',{}),True)
        self.assertEqual(my_cd(environ,'200 Ok',{}),True)

