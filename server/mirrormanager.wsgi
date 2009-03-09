#!/usr/bin/python
__requires__ = 'TurboGears[future]'
import pkg_resources
pkg_resources.require("TurboGears")
pkg_resources.require("CherryPy<3.0")

import sys
import turbogears
import cherrypy
import cherrypy._cpwsgi
import atexit
from os.path import exists, dirname, join

cherrypy.lowercase_api = True

conffiles = ('/etc/mirrormanager/prod.cfg',
             join(dirname(__file__),'dev.cfg'),
             join(dirname(__file__),'prod.cfg'))

for c in conffiles:
    if exists(c):
        turbogears.update_config(configfile=c, modulename="mirrormanager.config")
        break

import mirrormanager.controllers
cherrypy.root = mirrormanager.controllers.Root()

if cherrypy.server.state == 0:
    atexit.register(cherrypy.server.stop)
    cherrypy.server.start(init_only=True, server_class=None)

def application(environ, start_response):
    environ['SCRIPT_NAME'] = ''
    return cherrypy._cpwsgi.wsgiApp(environ, start_response)

