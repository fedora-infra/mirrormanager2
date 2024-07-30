import logging
from contextlib import suppress

import requests

from mirrormanager2 import __version__
from mirrormanager2 import lib as mmlib

from .connector import Connector, FetchingFailed, TryLater
from .constants import CONNECTION_TIMEOUT, REPODATA_FILE

logger = logging.getLogger(__name__)


class HTTPConnector(Connector):
    def _connect(self):
        session = requests.Session()
        session.headers = {
            "Connection": "Keep-Alive",
            "Pragma": "no-cache",
            "User-Agent": f"mirrormanager-crawler/{__version__} (+https://github.com/fedora-infra/mirrormanager2/)",
        }
        return session

    def _close(self):
        self._connection.close()

    def check_url(self, url):
        conn = self.get_connection()
        response = conn.head(url, timeout=CONNECTION_TIMEOUT)
        return response.ok

    def _check_file(self, conn, url, filedata, readable):
        """Returns tuple:
        True - URL exists
        False - URL doesn't exist
        None - we don't know
        """
        try:
            response = conn.head(url, timeout=CONNECTION_TIMEOUT)
            response.raise_for_status()
        except requests.Timeout as e:
            raise TryLater(f"HTTP timeout: {e}") from e
        except requests.HTTPError as e:
            response = e.response
            if response.status_code in (404, 410):
                # Not Found / Gone
                return False
            if response.status_code == 403:
                # may be a hidden dir still
                if readable:
                    # It should be readable but it's not
                    return False
                else:
                    # This 403 is allowed
                    return None
            logger.debug("Could not get the content length for %s: %s", url, response)
            return None
        except requests.RequestException as e:
            logger.debug("Could not get the content length for %s: %s", url, e)
            return None

        try:
            content_length = response.headers["Content-Length"]
        except KeyError:
            logger.debug("No content length header for %s", url)
            return True

        # lighttpd returns a Content-Length for directories
        # apache and nginx do not
        # For the basic check in check_for_base_dir() it is only
        # relevant if the directory exists or not. Therefore
        # passing None as filedata[]. This needs to be handled here.
        if filedata is None:
            # The file/directory seems to exist, no additional check possible
            return True
        # fixme should check last_modified too
        if float(filedata["size"]) != float(content_length):
            return False

        # handle streaming/chunked return or zero-length file
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
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            raise FetchingFailed() from e
        if not r.ok:
            raise FetchingFailed(r)
        return r.content


class HTTPSConnector(HTTPConnector):
    pass
