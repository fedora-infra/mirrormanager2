import cherrypy
from turbogears import controllers, expose
from mirrormanager.hostconfig import read_host_config
import bz2
import base64
import pickle

class XmlrpcController(controllers.Controller):
    def __init__(self):
        cherrypy.config.update({'xmlrpc_filter.on': True})

    @expose()
    def checkin(self, p):
        config = pickle.loads(bz2.decompress(base64.urlsafe_b64decode(p)))
        r, message = read_host_config(config)
        if r is not None:
            return message + 'checked in successful'
        else:
            return message + 'error checking in'
