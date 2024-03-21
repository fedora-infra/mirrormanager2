import hashlib
import logging

import backoff
from sqlalchemy.orm import object_session

from mirrormanager2 import lib as mmlib

logger = logging.getLogger(__name__)


class TryLater(Exception):
    pass


class ForbiddenExpected(Exception):
    pass


class SchemeNotAvailable(Exception):
    pass


class FetchingFailed(Exception):
    def __init__(self, response=None):
        self.response = response


def _on_backoff(details):
    # connector = details["args"][0]
    url = details["args"][1]
    logger.info(
        f"Server load exceeded on {url} - trying again in "
        f"{details['wait']:0.1f}s (after {details['tries']} tries)"
    )


def _on_giveup(details):
    # connector = details["args"][0]
    url = details["args"][1]
    logger.info(f"Server load exceeded on {url} - giving up after {details['tries']} tries")


class Connector:
    scheme = None

    def __init__(self, config, netloc, debuglevel, on_closed):
        self._config = config
        self._netloc = netloc
        self.debuglevel = debuglevel
        self._connection = None
        self._on_closed = on_closed

    def get_connection(self):
        if self._connection is None:
            self._connection = self._connect()
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

    @backoff.on_exception(
        backoff.expo,
        TryLater,
        max_tries=3,
        on_backoff=_on_backoff,
        on_giveup=_on_giveup,
        logger=None,  # custom logging
    )
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
        try:
            sha256 = self.get_sha256(graburl)
        except FetchingFailed:
            logger.debug("Could not get %s", graburl)
            return False
        session = object_session(directory)
        latest_file_detail = mmlib.get_file_detail(session, filename, directory_id=directory.id)
        if latest_file_detail is None:
            return False
        if latest_file_detail.sha256 != sha256:
            logger.debug(
                f"Found {filename} with sha {sha256}, but expected {latest_file_detail.sha256}"
            )
            return False
        return True

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
        try:
            dir_status = self.check_dir(dir_url, directory)
        except TryLater as e:
            # We backed off a few times but it's still in timeout
            raise SchemeNotAvailable from e
        # logger.debug(f"Dir status for {dir_url} is {dir_status}")
        return dir_status
