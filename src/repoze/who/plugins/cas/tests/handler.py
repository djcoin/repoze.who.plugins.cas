
from BaseHTTPServer import BaseHTTPRequestHandler

import urlparse


class Handler(BaseHTTPRequestHandler):
    """
    Very simple server used as a mock for a CAS server,
    just answering if a validate?ticket=XXX is present
    """
    def __init__(self, request, address, server):
        self.__server = server
        BaseHTTPRequestHandler.__init__(
                self, request, address, server)

    def do_GET(self):
        #print "\n ########### Getting : %s ############ \n" % self.path
        self.path = self.path[1:]

        if '__stop__' in self.path:
            raise SystemExit
        
        else:
            if self.path.startswith('validate'):
                self.path = self.path[len('validate')+1:]

                qs = urlparse.parse_qs(self.path)
                t = qs.get('ticket')
                if t != None: 
                    msg = ((t[0]=='valid' and ['yes\n', 'sim\n']) or
                       ['no\n', '\n'])
                    self.wfile.write("".join(msg))
                else:    
                    #from exception import Warning
                    #raise Warning("Your url contains validate, thus it \
                    #        should also contain a ticket key")
                    print "Your url contains validate, thus it \
                           should also contain a ticket key"
           
            elif self.path.startswith('logout'):
                pass


     

    #self.send_response(404, 'Not Found')
    #out = '<html><body>Not Found</body></html>'
    ##out = '\n'.join(self.tree, self.path, path)
    #self.send_header('Content-Length', str(len(out)))
    #self.send_header('Content-Type', 'text/html')
    #self.end_headers()
    #self.wfile.write(out)



