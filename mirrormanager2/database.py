from flask import g

from mirrormanager2 import lib as mmlib


class Database:
    def __init__(self, app=None):
        self.session = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.session = mmlib.create_session(app.config["DB_URL"])
        app.before_request(self._store_session)
        app.teardown_request(self._shutdown_session)

    def _store_session(self):
        g.db = self.session

    def _shutdown_session(self, exception=None):
        """Remove the DB session at the end of each request."""
        g.db = None
        self.session.remove()
