import logging
import os
from contextlib import contextmanager

from .threads import threadlocal
from .ui import get_logging_handler

logger = logging.getLogger(__name__)
thread_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
master_formatter = (
    # "%(levelname)s:%(name)s:%(hosts)s:%(threads)s:%(hostid)s:%(hostname)s:%(message)s"
    # "%(levelname)s:%(name)s:%(hostid)s:%(hostname)s:%(message)s"
    "%(hostname)s (%(hostid)s): %(message)s"
)


# To insert information about the number of hosts and threads in each master
# log message this filter is necessary
class MasterFilter(logging.Filter):
    def filter(self, record):
        # record.hosts = "Hosts(%d/%d)" % (current_host, all_hosts)
        # record.threads = "Threads(%d/%d)" % (threads_active, threads)
        try:
            record.hostid = threadlocal.host_id
            record.hostname = threadlocal.host_name
        except Exception:
            record.hostid = 0
            record.hostname = "master"
        return True


# This filter is necessary to enable logging per thread into a separate file
# Based on http://plumberjack.blogspot.de/2010/09/configuring-logging-for-web.html
class InjectingFilter(logging.Filter):
    """Check that the treadlocal variable has the attributes we want.

    Example: InjectingFilter(host_id=42) will only log if threadlocal.host_id == 42
    """

    def __init__(self, **kwargs):
        self.args = kwargs

    def filter(self, record):
        try:
            return all(getattr(threadlocal, key) == value for key, value in self.args.items())
        except Exception:
            return False


def setup_logging(debug, console):
    handler = get_logging_handler(console)
    f = MasterFilter()
    handler.addFilter(f)
    logging.basicConfig(
        format=master_formatter,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[handler],
        level=logging.DEBUG if debug else logging.INFO,
    )
    # Set the requests loggers to INFO, otherwise they are very noisy
    if debug:
        for logger_name in ("requests", "urllib3"):
            logging.getLogger(logger_name).setLevel(logging.INFO)


@contextmanager
def thread_file_logger(config, host_id, debug):
    log_dir = config.get("MM_LOG_DIR", None)
    if log_dir is None or log_dir == "-":
        return
    log_dir = os.path.join(log_dir, "crawler")
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"{host_id}.log")
    handler = logging.FileHandler(log_file)
    f = InjectingFilter(host_id=host_id)
    handler.addFilter(f)

    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    handler.setFormatter(thread_formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    yield log_file

    root_logger.removeHandler(handler)
