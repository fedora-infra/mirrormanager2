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
    def __init__(self, config, debuglevel=0, timeout=600):
        self._connections = {}
        self.config = config
        self.debuglevel = debuglevel
        self.timeout = timeout

    def get(self, url):
        scheme, netloc, path, query, fragment = urlsplit(url)
        if (scheme, netloc) not in self._connections:
            try:
                connection_class = _get_connection_class(scheme)
            except ValueError:
                logger.error(f"Malformed URL: {url!r}")
                raise
            self._connections[(scheme, netloc)] = connection_class(
                config=self.config,
                netloc=netloc,
                debuglevel=self.debuglevel,
                timeout=self.timeout,
                on_closed=partial(self._remove_connection, scheme, netloc),
            )
            # self._connections[(scheme, netloc)] = self._connect(netloc)
            # self._connections[(scheme, netloc)].set_debuglevel(self.debuglevel)
        return self._connections[(scheme, netloc)]

    def close(self, url):
        scheme, netloc, path, query, fragment = urlsplit(url)
        try:
            connection = self._connections[(scheme, netloc)]
        except KeyError:
            return
        connection.close()

    def _remove_connection(self, scheme, netloc, connection):
        del self._connections[(scheme, netloc)]

    def close_all(self):
        for connection in list(self._connections.values()):
            connection.close()
        self._connections = {}
