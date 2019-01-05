#!/usr/bin/env python

# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.8', 'jinja2 >= 2.4']
import pkg_resources

import argparse
import sys
import os


parser = argparse.ArgumentParser(
    description='Run the mirrormanager2 app')
parser.add_argument(
    '--config', '-c', dest='config',
    help='Configuration file to use.')
parser.add_argument(
    '--debug', dest='debug', action='store_true',
    default=False,
    help='Expand the level of data returned.')
parser.add_argument(
    '--profile', dest='profile', action='store_true',
    default=False,
    help='Profile the web application.')
parser.add_argument(
    '--port', '-p', default=5000,
    help='Port for the flask application.')
parser.add_argument(
    '--host', default="127.0.0.1",
    help='Hostname to listen on. When set to 0.0.0.0 the server is available \
    externally. Defaults to 127.0.0.1 making the it only visable on localhost')

args = parser.parse_args()

if args.config:
    config = args.config
    if not config.startswith('/'):
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        config = os.path.join(here, config)
    os.environ['MM2_CONFIG'] = config

from mirrormanager2.app import APP

if args.profile:
    from werkzeug.contrib.profiler import ProfilerMiddleware
    APP.config['PROFILE'] = True
    APP.wsgi_app = ProfilerMiddleware(APP.wsgi_app, restrictions=[30])

APP.debug = True
APP.run(port=int(args.port), host=args.host)
