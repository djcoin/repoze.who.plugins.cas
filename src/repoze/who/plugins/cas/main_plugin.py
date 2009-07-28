
import urlparse
import urllib
import cgi

from paste.httpheaders import CONTENT_LENGTH
from paste.httpheaders import CONTENT_TYPE
from paste.httpheaders import LOCATION
from paste.httpexceptions import HTTPFound
from paste.httpexceptions import HTTPUnauthorized
from paste.httpexceptions import HTTPTemporaryRedirect
from paste.request import parse_dict_querystring
from paste.request import parse_formvars
from paste.request import construct_url
from paste.request import parse_querystring

from paste.response import header_value

from zope.interface import implements

from repoze.who.interfaces import IChallenger, IIdentifier, IAuthenticator

import re

__MYDEBUG__ = False

class FormPluginBase(object):
    def _get_rememberer(self, environ):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer

    #### IIdentifier ####
    def remember(self, environ, identity):
        rememberer = self._get_rememberer(environ)
        return rememberer.remember(environ, identity)

    #### IIdentifier ####
    def forget(self, environ, identity):
        rememberer = self._get_rememberer(environ)
        return rememberer.forget(environ, identity) 

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, id(self))

# Former redirectingFormPlugin
class CASChallengePlugin(FormPluginBase):

    implements(IChallenger, IIdentifier, IAuthenticator)
    
    def __init__(self, cas_url,
                 path_logout,
                 path_toskip,
                 rememberer_name):
        self.cas_url = cas_url
        self.path_logout = path_logout
        self.path_toskip = path_toskip
        # rememberer_name is the name of another configured plugin which
        # implements IIdentifier, to handle remember and forget duties
        # (ala a cookie plugin or a session plugin)
        self.rememberer_name = rememberer_name

    #### IChallenger ####
    def challenge(self, environ, status, app_headers, forget_headers):

# this challenge consist in loggin out
        if environ.has_key('rwpc.logout'): 
# FIXME : maybe this Location should replace the key rwpc.logout
            if __MYDEBUG__: print "Avant : " + app_headers.__str__()
            app_headers = [(a,b) for a,b in app_headers if a.lower() != 'location' ]
            if __MYDEBUG__: print "Apres : " + app_headers.__str__()


            headers=[('Location',self.cas_url + 'logout?service=' +
                                  urllib.quote(environ['rwpc.logout']))]
            headers = headers + app_headers + forget_headers
            if __MYDEBUG__: print('########' + headers.__str__() + '###########')
            return HTTPFound(headers=headers)

# ELSE, perform a real challenge => asking for loggin
# here by redirecting the user on CAS.  

# what we do is just adding a ?service=... on the  casurl/login path
        cas_url = self.cas_url + "?service=" + urllib.quote(self._serviceURL(environ))

        if __MYDEBUG__ : print "##############" + cas_url + "#############"
        headers = [ ('Location', cas_url) ] #+ 'login'
        cookies = [(h,v) for (h,v) in app_headers if h.lower() == 'set-cookie']
        headers = headers + forget_headers + cookies

        return HTTPFound(headers=headers)

# the request has to go throught all the process
##
# bhp => logout callback from CAS
# logout regex => logout
# to skip => skip
# ticket => validate
    #### IIdentifier ####
    def identify(self, environ):
# WARNING : does not completely check the uri => should use construct_url
        #path_info = environ['PATH_INFO']
        #path_script = environ['SCRIPT_NAME']
        #uri  =  path_script + path_info
        uri = environ.get('REQUEST_URI',construct_url(environ))

        query = parse_dict_querystring(environ)
# This cgi parameter is set if this is a callback from the CAS server after 
# having perform a logout
        if query.get('bhp',None):
# we could get rid of this parameter..
            return None

# path_logout for every app. 
# 1/ A first redirection will disconnect from the CAS 
#    (passing in service=intended_url_callback_
# 2/ The URL will finally perform normally
        for regex in self.path_logout:
           if re.match(regex, uri) != None:
               if __MYDEBUG__ : print "LOGOUT #### "
               # we've been asked to perform a logout

# use all except : POST
# trigger the challenge and tells the challenge this is a logout
               query['bhp'] = 'go'
               environ['rwpc.logout'] = \
                    self._serviceURL(environ,urllib.urlencode(query))
               
               return None

# skipping, whatever it is (loggin, validating ticket etc.)
# except for logout (see above)
        for regex in self.path_toskip:
            if re.match(regex, uri) != None:
                if __MYDEBUG__ : print "########### SKIPPING"
                return None

# one use ticket, try to validate
        t = query.pop('ticket',None)
        if t:
            if __MYDEBUG__ : print "Retrieving credentials : calling cas, calidate"
            credentials = self._validate(t,environ,query)
            return credentials

# construct an url 
    def _validate(self, ticket,environ,query):
        val_url = self.cas_url + "validate" + \
         '?service=' + urllib.quote(self._serviceURL(environ,
             urllib.urlencode(query))) + \
         '&ticket=' + urllib.quote(ticket)

        #import pdb; pdb.set_trace()

        r = urllib.urlopen(val_url).readlines()   # returns 2 lines
        if __MYDEBUG__ : print r
        if len(r) == 2 and re.match("yes", r[0]) != None:
            return {'login' : r[1].strip(),
                    'password': ''}
        return None

# @return
# used 2 times : one to get the ticket, the other to validate it
    def _serviceURL(self,environ,qs=None):
        if qs != None:
            url = construct_url(environ, querystring=qs)
        else:
            url = construct_url(environ)
        return url
#paste.request.construct_url(environ, with_query_string=True, with_path_info=True, script_name=None, path_info=None, querystring=None)

    #### IAuthenticatorPlugin #### 
    def authenticate(self, environ, identity):
# actually does nothing => the CAS has already 
# check the login/pass for us.
        return identity.get('login',None)


def make_plugin(cas_url=None, # url for the cas
                             rememberer_name=None, # plugin for remember
                             path_logout= '', # regex url to logout
                             path_toskip=''): # regex url to skip
    
    if cas_url is None:
        raise ValueError(
            'must include login_form_url in configuration')

    if rememberer_name is None:
        raise ValueError(
             'must include rememberer_name in configuration')
    path_logout = path_logout.lstrip().split('\n');
    path_toskip = path_toskip.lstrip().splitlines()

    plugin = CASChallengePlugin(cas_url,path_logout,path_toskip,rememberer_name)
    return plugin

# came_from = re.sub(r'ticket=[^&]*&?', '', came_from)

