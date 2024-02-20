import logging
import os

from rich.logging import RichHandler

from .threads import get_thread_id, threadlocal

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
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
    def __init__(self, thread_id):
        self.thread_id = thread_id

    def filter(self, record):
        try:
            return threadlocal.thread_id == self.thread_id
        except Exception:
            return False


def setup_logging(debug, console):
    handler = RichHandler(console=console, rich_tracebacks=True)
    f = MasterFilter()
    handler.addFilter(f)
    logging.basicConfig(
        format=master_formatter, handlers=[handler], level=logging.DEBUG if debug else logging.INFO
    )


def thread_file_logger(log_dir, host_id, debug):
    # check if the directory exists
    if log_dir is not None:
        log_dir += "/crawler"
        if not os.path.isdir(log_dir):
            # MM_LOG_DIR/crawler seems to be configured but does not exist
            # not logging
            logger.warning("Directory " + log_dir + " does not exists." " Not logging per host")
            log_dir = None

    log_file = None
    fh = None
    if log_dir is not None:
        log_file = log_dir + "/" + str(host_id) + ".log"
        fh = logging.FileHandler(log_file)
        threadlocal.thread_id = get_thread_id()
        f = InjectingFilter(get_thread_id())
        fh.addFilter(f)

        if debug:
            fh.setLevel(logging.DEBUG)
        else:
            fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(fh)

    return log_file, fh
