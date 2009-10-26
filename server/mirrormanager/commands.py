#!/usr/bin/python
import pkg_resources
import cherrypy
pkg_resources.require("TurboGears")

import turbogears
cherrypy.lowercase_api = True

from os.path import exists, join
import os
import sys

def start():
    cherrypy.lowercase_api = True
    # first look on the command line for a desired config file,
    # if it's not on the command line, then
    # look for setup.py in this directory. If it's not there, this script is
    # probably installed
    if len(sys.argv) > 1:
        turbogears.update_config(configfile=sys.argv[1], 
            modulename="mirrormanager.config")
    elif exists(join(os.getcwd(), "setup.py")):
        turbogears.update_config(configfile="dev.cfg",
            modulename="mirrormanager.config")
    else:
        turbogears.update_config(configfile="/etc/mirrormanager/prod.cfg",
            modulename="mirrormanager.config")

    from mirrormanager.controllers import Root

    turbogears.start_server(Root())
