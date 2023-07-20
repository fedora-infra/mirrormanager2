#!/usr/bin/env python

from mirrormanager2.app import create_app
from mirrormanager2.lib import model

app = create_app()
model.create_tables(
    app.config["DB_URL"], app.config.get("PATH_ALEMBIC_INI", None), debug=True
)
