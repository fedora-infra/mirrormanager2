import ftplib
import logging
from contextlib import suppress
from ftplib import FTP
from urllib.parse import urlsplit

from mirrormanager2 import lib as mmlib

from .connector import Connector, TryLater

logger = logging.getLogger(__name__)


class FTPConnector(Connector):
    def _connect(self):
        conn = FTP(self.netloc, timeout=self.timeout)
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
        if i > 1:
            raise TryLater()

        try:
            listing = self._ftp_dir(url)
        except ftplib.error_perm as e:
            # Returned by Princeton University when directory does not exist
            if str(e).startswith("550"):
                return []
            # Returned by Princeton University when directory isn't readable
            # (pre-bitflip)
            if str(e).startswith("553"):
                if readable:
                    return []
                else:
                    return None
            # Returned by ftp2.surplux.net when cannot log in due to connection
            # restrictions
            if str(e).startswith("530"):
                self.close_ftp(url)
                return self.get_ftp_dir(url, readable, i + 1)
            if str(e).startswith("500"):  # Oops
                raise TryLater() from e
            else:
                logger.error(f"unknown permanent error {e} on {url}")
                raise
        except ftplib.error_temp as e:
            # Returned by Boston University when directory does not exist
            if str(e).startswith("450"):
                return []
            # Returned by Princeton University when cannot log in due to
            # connection restrictions
            if str(e).startswith("421"):
                logger.info("Connections Exceeded %s" % url)
                raise TryLater() from e
            if str(e).startswith("425"):
                logger.info("Failed to establish connection on %s" % url)
                raise TryLater() from e
            else:
                logger.error(f"unknown error {e} on {url}")
                raise
        except (OSError, EOFError):
            self.close(url)
            return self.get_ftp_dir(url, readable, i + 1)

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
        if results is None:
            return None

        with mmlib.instance_attribute(directory, "files") as files:
            # Getting Directory.files is a bit expensive, involves json decoding
            for filename in files:
                status = self._check_file(results[filename], files[filename])
                if not status:
                    # Shortcut: we don't need to go over other files
                    return False
        return True
