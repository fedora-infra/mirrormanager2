#!/usr/bin/env python

# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from mirrormanager2.app import APP
from mirrormanager2.lib import model

model.create_tables(
    APP.config['DB_URL'],
    APP.config.get('PATH_ALEMBIC_INI', None),
    debug=True)
