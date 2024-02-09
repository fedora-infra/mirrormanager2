import logging
from contextlib import suppress

import requests

from .connector import Connector, FetchingFailed, ForbiddenExpected
from .constants import HTTP_TIMEOUT

logger = logging.getLogger("crawler")


class HTTPConnector(Connector):
    def _connect(self, netloc):
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
        conn = self.open(url)
        response = conn.head(url, timeout=HTTP_TIMEOUT)
        return response.ok

    def _get_content_length(self, conn, url, readable, recursion=0, retry=0):
        response = conn.head(url, timeout=HTTP_TIMEOUT)
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
        except Exception:
            return False
        # lighttpd returns a Content-Length for directories
        # apache and nginx do not
        # For the basic check in check_for_base_dir() it is only
        # relevant if the directory exists or not. Therefore
        # passing None as filedata[]. This needs to be handled here.
        if filedata is None:
            # The file/directory seems to exist
            return True
        # fixme should check last_modified too
        if content_length not in (None, False) and float(filedata["size"]) != float(content_length):
            return False

        # handle no content-length header, streaming/chunked return
        # or zero-length file
        return True

    def _check_dir(self, url, directory):
        try:
            conn = self.open(url)
        except Exception as e:
            logger.info(f"Could not get {url}: {e}")
            return None
        for filename in directory.files:
            file_url = f"{url}/{filename}"
            exists = self._check_file(conn, file_url, directory.files[filename], directory.readable)
            if filename == "repomd.xml" and exists:
                # Additional optional check
                with suppress(Exception):
                    exists = self.compare_sha256(directory, filename, file_url)
            if exists in (False, None):
                # Shortcut: we don't need to go over other files
                return exists
        return True

    def _get_file(self, url):
        conn = self.open(url)
        try:
            r = conn.get(
                url,
                timeout=HTTP_TIMEOUT,
            )
        except requests.exceptions.ConnectionError as e:
            raise FetchingFailed() from e
        if not r.ok:
            raise FetchingFailed(r)
        return r.content


class HTTPSConnector(HTTPConnector):
    pass
