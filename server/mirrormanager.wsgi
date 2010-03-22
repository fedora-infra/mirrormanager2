#!/usr/bin/python
__requires__ = 'TurboGears[future]'
import sys
sys.stdout = sys.stderr
sys.path.append('/usr/share/mirrormanager/server/')

import pkg_resources
pkg_resources.require("TurboGears")
pkg_resources.require("CherryPy<3.0")

import turbogears
from turbogears import startup
import cherrypy
import cherrypy._cpwsgi
import atexit
from os.path import exists, dirname, join
from fedora.tg.tg1utils import enable_csrf

cherrypy.lowercase_api = True

conffiles = ('/etc/mirrormanager/prod.cfg',
             join(dirname(__file__),'dev.cfg'),
             join(dirname(__file__),'prod.cfg'))

for c in conffiles:
    if exists(c):
        turbogears.update_config(configfile=c, modulename="mirrormanager.config")
        break

# as a WSGI, we need to force these settings
turbogears.config.update({'global': {'server.environment': 'production'}})
turbogears.config.update({'global': {'autoreload.on': False}})
turbogears.config.update({'global': {'server.log_to_screen': False}})

startup.call_on_startup.append(enable_csrf)

import mirrormanager.controllers
cherrypy.root = mirrormanager.controllers.Root()

if cherrypy.server.state == 0:
    atexit.register(cherrypy.server.stop)
    cherrypy.server.start(init_only=True, server_class=None)

def application(environ, start_response):
    environ['SCRIPT_NAME'] = ''
    return cherrypy._cpwsgi.wsgiApp(environ, start_response)

