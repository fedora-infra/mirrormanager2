import logging
from functools import partial
from urllib.parse import urlsplit

from .ftp_connector import FTPConnector
from .http_connector import HTTPConnector, HTTPSConnector
from .rsync_connector import RsyncConnector

logger = logging.getLogger(__name__)


def _get_connection_class(scheme):
    if scheme == "http":
        return HTTPConnector
    if scheme == "https":
        return HTTPSConnector
    if scheme == "ftp":
        return FTPConnector
    if scheme == "rsync":
        return RsyncConnector
    raise ValueError(f"Unknown scheme: {scheme}")


class ConnectionPool:
    def __init__(self, config, debuglevel=0):
        self._connections = {}
        self.config = config
        self.debuglevel = debuglevel

    def _get_key(self, url):
        scheme, netloc, path, query, fragment = urlsplit(url)
        if scheme == "rsync":
            module = path.split("/")[1]
            return (scheme, netloc, module)
        else:
            return (scheme, netloc)

    def get(self, url):
        scheme, netloc, path, query, fragment = urlsplit(url)
        key = self._get_key(url)
        if key not in self._connections:
            try:
                connection_class = _get_connection_class(scheme)
            except ValueError:
                logger.error(f"Malformed URL: {url!r}")
                raise
            self._connections[key] = connection_class(
                config=self.config,
                netloc=netloc,
                debuglevel=self.debuglevel,
                on_closed=partial(self._remove_connection, key),
            )
            # self._connections[key] = self._connect(netloc)
            # self._connections[key].set_debuglevel(self.debuglevel)
        return self._connections[key]

    def close(self, url):
        key = self._get_key(url)
        try:
            connection = self._connections[key]
        except KeyError:
            return
        connection.close()

    def _remove_connection(self, key, connection):
        del self._connections[key]

    def close_all(self):
        for connection in list(self._connections.values()):
            connection.close()
        self._connections = {}
