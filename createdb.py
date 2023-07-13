#!/usr/bin/env python

from mirrormanager2.app import APP
from mirrormanager2.lib import model

model.create_tables(
    APP.config['DB_URL'],
    APP.config.get('PATH_ALEMBIC_INI', None),
    debug=True)
