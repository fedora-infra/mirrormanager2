#!/usr/bin/python
__requires__ = 'TurboGears[future]'
import pkg_resources
pkg_resources.require("TurboGears")

import turbogears
from turbogears import startup

import cherrypy
cherrypy.lowercase_api = True

from os.path import *
import sys
from fedora.tg.util import enable_csrf

# first look on the command line for a desired config file,
# if it's not on the command line, then
# look for setup.py in this directory. If it's not there, this script is
# probably installed
if len(sys.argv) > 1:
    turbogears.update_config(configfile=sys.argv[1], 
        modulename="mirrormanager.config")
elif exists(join(dirname(__file__), "setup.py")):
    turbogears.update_config(configfile="dev.cfg",
        modulename="mirrormanager.config")
else:
    turbogears.update_config(configfile="prod.cfg",
        modulename="mirrormanager.config")

startup.call_on_startup.append(enable_csrf)

from mirrormanager.controllers import Root
import mirrormanager.mirrorlist

turbogears.start_server(Root())
