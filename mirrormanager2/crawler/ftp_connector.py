import ftplib
import logging
from contextlib import suppress
from ftplib import FTP
from urllib.parse import urlsplit

from mirrormanager2 import lib as mmlib

from .connector import Connector, TryLater
from .constants import CONNECTION_TIMEOUT
from .states import DirStatus

logger = logging.getLogger(__name__)


class FTPConnector(Connector):
    def _connect(self):
        conn = FTP(self.netloc, timeout=CONNECTION_TIMEOUT)
        conn.set_debuglevel(self.debuglevel)
        conn.login()
        return conn

    def _close(self):
        with suppress(Exception):
            self._connection.quit()

    def _ftp_dir(self, url):
        try:
            conn = self.get_connection()
        except Exception:
            return None
        scheme, netloc, path, query, fragment = urlsplit(url)
        results = []

        def _callback(line):
            if self.debuglevel > 0:
                logger.info(line)
            results.append(line)

        conn.dir(path, _callback)
        return results

    def get_ftp_dir(self, url, readable, i=0):
        """Return the directory listing as a dict, or a DirStatus.

        A DirStatus is returned when the server's answer already decides the
        directory's state and there is no listing to compare files against.
        """
        if i > 1:
            raise TryLater("Too many FTP 530 errors")

        try:
            listing = self._ftp_dir(url)
        except ftplib.error_perm as e:
            # Returned by Princeton University when directory does not exist
            if str(e).startswith("550"):
                return DirStatus.ABSENT
            # Returned by Princeton University when directory isn't readable
            # (pre-bitflip)
            if str(e).startswith("553"):
                if readable:
                    # It should be readable but it's not
                    return DirStatus.STALE
                else:
                    # This 553 is allowed
                    return DirStatus.UNKNOWN
            # Returned by ftp2.surplux.net when cannot log in due to connection
            # restrictions
            if str(e).startswith("530"):
                self.close_ftp(url)
                return self.get_ftp_dir(url, readable, i + 1)
            if str(e).startswith("500"):  # Oops
                raise TryLater(f"Got FTP 500 error: {e}") from e
            else:
                logger.error(f"unknown permanent error {e} on {url}")
                raise
        except ftplib.error_temp as e:
            # Returned by Boston University when directory does not exist
            if str(e).startswith("450"):
                return DirStatus.ABSENT
            # Returned by Princeton University when cannot log in due to
            # connection restrictions
            if str(e).startswith("421"):
                logger.info("Connections Exceeded %s", url)
                raise TryLater(f"FTP error 421: {e}") from e
            if str(e).startswith("425"):
                logger.info("Failed to establish connection on %s", url)
                raise TryLater(f"FTP error 425: {e}") from e
            else:
                logger.error(f"unknown error {e} on {url}")
                raise
        except (OSError, EOFError):
            self.close(url)
            return self.get_ftp_dir(url, readable, i + 1)

        if listing is None:
            # _ftp_dir() could not connect at all.
            return DirStatus.UNKNOWN
        results = {}
        for line in listing:
            if line.startswith("total"):
                # some servers first include a line starting with the word 'total'
                # that we can ignore
                continue
            fields = line.split()
            try:
                results[fields[8]] = {"size": fields[4]}
            except IndexError:  # line doesn't have 8 fields, it's not a dir line
                pass
        return results

    def compare_sha256(self, d, filename, graburl):
        return True  # Not implemented on FTP

    def _check_file(self, current_file_info, db_file_info):
        try:
            return float(current_file_info["size"]) == float(db_file_info["size"])
        except Exception:
            return False

    def _check_dir(self, url, directory):
        results = self.get_ftp_dir(url, directory.readable)
        if isinstance(results, DirStatus):
            # The server's answer already decided the state, there is no
            # listing to compare files against.
            return results

        with mmlib.instance_attribute(directory, "files") as files:
            # Getting Directory.files is a bit expensive, involves json decoding
            # files can be None in case of empty directories
            files = files or []
            if not files:
                # The directory holds no files on the master, so there is
                # nothing to compare. Whether it is up to date is decided
                # from its child directories after the scan.
                return DirStatus.PRESENT
            for filename in files:
                if filename not in results:
                    return DirStatus.STALE  # Missing file, no need to go over other files
                status = self._check_file(results[filename], files[filename])
                if not status:
                    # Shortcut: we don't need to go over other files
                    return DirStatus.STALE
        return DirStatus.UP2DATE
