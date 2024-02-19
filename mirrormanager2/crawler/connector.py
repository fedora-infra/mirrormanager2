import hashlib
import logging
from urllib.parse import urlsplit

logger = logging.getLogger("crawler")


class TryLater(Exception):
    pass


class ForbiddenExpected(Exception):
    pass


class SchemeNotAvailable(Exception):
    pass


class FetchingFailed(Exception):
    def __init__(self, response=None):
        self.response = response


class Connector:
    scheme = None

    def __init__(self, config, debuglevel, timeout, on_closed):
        self._config = config
        self.debuglevel = debuglevel
        # ftplib and httplib take the timeout in seconds
        self.timeout = timeout
        self._connection = None
        self._on_closed = on_closed

    def open(self, url):
        scheme, netloc, path, query, fragment = urlsplit(url)
        self._connection = self._connect(netloc)
        return self._connection

    def close(self):
        if self._connection is not None:
            self._close()
        self._on_closed(self)

    def _connect(self, url):
        raise NotImplementedError

    def _close(self):
        raise NotImplementedError

    def _get_file(self, url):
        raise NotImplementedError

    # TODO: backoff on TryAgain with message
    # f"Server load exceeded on {host!r} - try later ({try_later_delay} seconds)"
    def check_dir(self, url, directory):
        return self._check_dir(url, directory)

    def _check_dir(self, url, directory):
        raise NotImplementedError

    def get_sha256(self, graburl):
        """looks for a FileDetails object that matches the given URL"""
        contents = self._get_file(graburl)
        return hashlib.sha256(contents).hexdigest()

    def compare_sha256(self, directory, filename, graburl):
        """looks for a FileDetails object that matches the given URL"""
        found = False
        try:
            sha256 = self.get_sha256(graburl)
        except FetchingFailed:
            logger.debug("Could not get %s", graburl)
            return False
        for fd in list(directory.fileDetails):
            if fd.filename == filename and fd.sha256 is not None:
                if fd.sha256 == sha256:
                    found = True
                    break
                else:
                    logger.debug(f"Found {fd.filename} with sha {sha256}, but expected {fd.sha256}")
        return found

    def _get_dir_url(self, url, directory, category_prefix_length):
        dirname = directory.name[category_prefix_length:]
        return f"{url}/{dirname}"

    def check_category(
        self,
        url,
        directory,
        category_prefix_length,
    ):
        dir_url = self._get_dir_url(url, directory, category_prefix_length)
        dir_status = self.check_dir(dir_url, directory)
        if dir_status is None:
            # could be a dir with no files, or an unreadable dir.
            # defer decision on this dir, let a child decide.
            raise SchemeNotAvailable
        # logger.debug(f"Dir status for {dir_url} is {dir_status}")
        return dir_status
