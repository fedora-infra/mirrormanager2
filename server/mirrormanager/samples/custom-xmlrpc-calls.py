# http://www.dalkescientific.com/writings/diary/archive/2006/10/24/xmlrpc_in_turbogears.html

import sys
import xmlrpclib
import cherrypy
import turbogears
from turbogears import controllers

class RPCRoot(controllers.Controller):
    @turbogears.expose()
    def index(self):
        params, method = xmlrpclib.loads(cherrypy.request.body.read())
        try:
            if method == "index":
                # prevent recursion
                raise AssertionError("method cannot be 'index'")
            # Get the function and make sure it's exposed.
            method = getattr(self, method, None)
            # Use the same error message to hide private method names
            if method is None or not getattr(method, "exposed", False):
                raise AssertionError("method does not exist")

            # Call the method, convert it into a 1-element tuple
            # as expected by dumps                       
            response = method(*params)
            response = xmlrpclib.dumps((response,), methodresponse=1)
        except xmlrpclib.Fault, fault:
            # Can't marshal the result
            response = xmlrpclib.dumps(fault)
        except:
            # Some other error; send back some error info
            response = xmlrpclib.dumps(
                xmlrpclib.Fault(1, "%s:%s" % (sys.exc_type, sys.exc_value))
                )

        cherrypy.response.headers["Content-Type"] = "text/xml"
        return response

    # User-defined functions must use cherrypy.expose; turbogears.expose
    # does additional checking of the response type.
    @cherrypy.expose
    def add(self, a, b):
        return a+b

class Root(controllers.RootController):
    RPC2 = RPCRoot()
