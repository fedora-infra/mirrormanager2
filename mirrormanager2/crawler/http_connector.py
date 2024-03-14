import logging
from contextlib import suppress

import requests

from mirrormanager2 import lib as mmlib

from .connector import Connector, FetchingFailed, ForbiddenExpected, TryLater
from .constants import CONNECTION_TIMEOUT, REPODATA_FILE

logger = logging.getLogger(__name__)


class HTTPConnector(Connector):
    def _connect(self):
        session = requests.Session()
        session.headers = {
            "Connection": "Keep-Alive",
            "Pragma": "no-cache",
            "User-Agent": "mirrormanager-crawler/0.1 (+https://"
            "github.com/fedora-infra/mirrormanager2/)",
        }
        return session

    def _close(self):
        self._connection.close()

    def check_url(self, url):
        conn = self.get_connection()
        response = conn.head(url, timeout=CONNECTION_TIMEOUT)
        return response.ok

    def _get_content_length(self, conn, url, readable, recursion=0, retry=0):
        response = conn.head(url, timeout=CONNECTION_TIMEOUT)
        if response.ok:
            try:
                return response.headers["Content-Length"]
            except KeyError:
                return None
        if response.status_code == 404 or response.status_code == 410:
            # Not Found / Gone
            return False
        if response.status_code == 403:
            # may be a hidden dir still
            if readable:
                return False
            else:
                raise ForbiddenExpected()
        response.raise_for_status()

    def _check_file(self, conn, url, filedata, readable):
        """Returns tuple:
        True - URL exists
        False - URL doesn't exist
        None - we don't know
        """
        try:
            content_length = self._get_content_length(conn, url, readable)
        except ForbiddenExpected:
            return None
        except requests.Timeout as e:
            raise TryLater from e
        except Exception:
            return None
        # lighttpd returns a Content-Length for directories
        # apache and nginx do not
        # For the basic check in check_for_base_dir() it is only
        # relevant if the directory exists or not. Therefore
        # passing None as filedata[]. This needs to be handled here.
        if filedata is None:
            # The file/directory seems to exist, no additional check possible
            return True
        # fixme should check last_modified too
        if content_length not in (None, False) and float(filedata["size"]) != float(content_length):
            return False

        # handle no content-length header, streaming/chunked return
        # or zero-length file
        return True

    def _check_dir(self, url, directory):
        try:
            conn = self.get_connection()
        except Exception as e:
            logger.info(f"Could not get {url}: {e}")
            return None
        with mmlib.instance_attribute(directory, "files") as files:
            # Getting Directory.files is a bit expensive, involves json decoding
            for filename in files:
                file_url = f"{url}/{filename}"
                exists = self._check_file(conn, file_url, files[filename], directory.readable)
                if filename == REPODATA_FILE and exists:
                    # Additional optional check
                    with suppress(Exception):
                        exists = self.compare_sha256(directory, filename, file_url)
                if exists in (False, None):
                    # Shortcut: we don't need to go over other files
                    return exists
        return True

    def _get_file(self, url):
        conn = self.get_connection()
        try:
            r = conn.get(
                url,
                timeout=CONNECTION_TIMEOUT,
            )
        except requests.exceptions.ConnectionError as e:
            raise FetchingFailed() from e
        if not r.ok:
            raise FetchingFailed(r)
        return r.content


class HTTPSConnector(HTTPConnector):
    pass
