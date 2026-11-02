import logging
from contextlib import suppress
from urllib.parse import urljoin, urlsplit

import requests

from mirrormanager2 import __version__
from mirrormanager2 import lib as mmlib

from .connector import Connector, FetchingFailed, TryLater
from .constants import CONNECTION_TIMEOUT, REPODATA_FILE

logger = logging.getLogger(__name__)


def _changes_scheme(url, location):
    """Whether following `location` from `url` would leave the scheme."""
    if not location:
        return False
    return urlsplit(urljoin(url, location)).scheme != urlsplit(url).scheme


def _is_scheme_redirect(url, response):
    """Report whether the response sends us to a different scheme.

    A mirror is listed with the scheme it registered, so content registered
    under an http URL has to be served over http. An http URL which only
    works by redirecting to https is of no use to somebody who asked for
    http, for example to let a caching proxy do its work. Such a host has to
    register the https URL instead.

    A redirect which stays on the same scheme is not a problem and is not
    reported. Asking for a directory without a trailing slash is answered
    with a redirect to the same URL with one by every common web server, and
    that is how most URLs are registered.
    """
    if not 300 <= response.status_code < 400:
        return False
    location = response.headers.get("Location", "")
    if not _changes_scheme(url, location):
        return False
    logger.info(
        "%s returns %s and redirects to %s, which is a different scheme. The "
        "content has to be available on the URL which is registered, so please "
        "register that URL instead.",
        url,
        response.status_code,
        location,
    )
    return True


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
        # This is a directory, so ask for it with a trailing slash. Without
        # one every common web server answers with a redirect which adds it,
        # and a server behind TLS termination which does not look at
        # X-Forwarded-Proto builds that redirect with the wrong scheme. That
        # is not the mirror refusing to serve the scheme it registered, it is
        # just a badly built redirect, and the content is there.
        if not url.endswith("/"):
            url += "/"
        response = conn.head(url, timeout=CONNECTION_TIMEOUT)
        if _is_scheme_redirect(url, response):
            return False
        # This check only has to find the mirrors which dropped the content,
        # and those answer with a 404. Anything else means there is still
        # something at this path: a 403 from a directory which is not
        # listable, or a 502 from a server which cannot build the listing but
        # does serve the files below it. Whether those files are there and up
        # to date is decided per file, and a file which cannot be read leaves
        # the directory undecided instead of marking it up to date.
        return response.status_code not in (404, 410)

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

        if _is_scheme_redirect(url, response):
            # The content is not served on this URL at all. The Content-Length
            # below would be the one of the redirect page, so this has to be
            # caught before looking at it.
            return False

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
            # files can be None in case of empty directories
            files = files or []
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
        # Unlike head(), get() follows redirects. Same scheme redirects are
        # fine, but the content must not be fetched over another scheme than
        # the one which is registered.
        schemes = {urlsplit(hop.url).scheme for hop in r.history}
        schemes.add(urlsplit(r.url).scheme)
        if schemes != {urlsplit(url).scheme}:
            logger.info("%s was redirected to %s, which is a different scheme.", url, r.url)
            raise FetchingFailed(r)
        if not r.ok:
            raise FetchingFailed(r)
        return r.content


class HTTPSConnector(HTTPConnector):
    pass
