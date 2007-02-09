import cherrypy
from turbogears import controllers
from mirrors.hostconfig import *
import bz2
import base64
import pickle

class XmlrpcController(controllers.Controller):
    def __init__(self):
        cherrypy.config.update({'xmlrpc_filter.on': True,
                                'server.max_request_size': 1048576})


    def echo(self, data):
        return data
    echo.exposed = True

    def checkin(self, p):
        config = pickle.loads(bz2.decompress(base64.urlsafe_b64decode(p)))
        r = read_host_config(config)
        if r is not None:
            return 'checked in successful'
        else:
            return 'error checking in'
    checkin.exposed = True

    def good(self, pbz):
        return 'good'
    good.exposed = True
