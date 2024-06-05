import logging
import os
import time

from mirrormanager2 import lib as mmlib
from mirrormanager2.lib.sync import run_rsync

from .connector import Connector, SchemeNotAvailable

logger = logging.getLogger(__name__)


class RsyncConnector(Connector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scan_result = None

    def close(self):
        super().close()
        self._scan_result = None

    def _run(self, url):
        if not url.endswith("/"):
            url += "/"
        rsync_start_time = time.monotonic()
        try:
            result, listing = run_rsync(url, self._config["CRAWLER_RSYNC_PARAMETERS"], logger)
        except Exception:
            logger.exception("Failed to run rsync.", exc_info=True)
            return False
        rsync_stop_time = time.monotonic()
        logger.debug("rsync time: %s", int(rsync_stop_time - rsync_start_time))
        if result == 10:
            # no rsync content, fail!
            logger.info(
                "Connection to %s Refused.  Please check that the URL is "
                "correct and that the host has an rsync module still available.",
                url,
            )
            return False
        if result > 0:
            logger.info("rsync returned exit code %s", result)

        rsync = {}
        # put the rsync listing in a dict for easy access
        while True:
            line = listing.readline()
            if not line:
                break
            fields = line.split()
            try:
                rsync[fields[4]] = {
                    "mode": fields[0],
                    "size": fields[1],
                    "date": fields[2],
                    "time": fields[3],
                }
            except IndexError:
                logger.debug("invalid rsync line: %s\n" % line)

        # run_rsync() returns a temporary file which needs to be closed
        listing.close()

        logger.debug("rsync listing has %d lines" % len(rsync))
        return rsync

    def _check_file(self, current_file_info, db_file_info):
        if current_file_info["mode"].startswith("l"):
            # ignore symlink size differences
            return True

        try:
            return float(current_file_info["size"]) != float(db_file_info["size"])
        except ValueError:  # one of the conversion to float() failed
            logger.debug("Invalid size value for file %s", current_file_info)
            return False

    def _check_dir(self, dirname, directory):
        with mmlib.instance_attribute(directory, "files") as files:
            # Getting Directory.files is a bit expensive, involves json decoding
            for filename in sorted(files):
                if len(dirname) == 0:
                    key = filename
                else:
                    key = os.path.join(dirname, filename)
                logger.debug(f"Dirname: {dirname}, filename: {filename}, key: {key}")

                logger.debug("trying with key %s", key)
                try:
                    current_file_info = self._scan_result[key]
                except KeyError:  # file is not in the rsync listing
                    logger.debug("Missing remote file %s", key)
                    return False

                try:
                    status = self._check_file(current_file_info, files[filename])
                    if not status:
                        # Shortcut: we don't need to go over other files
                        return False
                except Exception as e:  # something else went wrong
                    logger.error("Exception caught when scanning %s: %s", filename, e)
                    return False

        return True

    def _get_dir_url(self, url, directory, category_prefix_length):
        # We don't need the whole URL, the scan has already been done
        return directory.name[category_prefix_length:]

    def check_category(
        self,
        url,
        directory,
        category_prefix_length,
    ):
        # Scan only once for the entire category
        if self._scan_result is None:
            self._scan_result = self._run(url)
        if not self._scan_result:
            # no rsync content, fail!
            raise SchemeNotAvailable
        return super().check_category(url, directory, category_prefix_length)
