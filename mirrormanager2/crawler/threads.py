import datetime
import hashlib
import logging
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from functools import partial

logger = logging.getLogger(__name__)

# Variable used to coordinate graceful shutdown of all threads
shutdown = False
# Maximum global execution time
max_global_execution_dt = None

# This is a "thread local" object that allows us to store the start time of
# each worker thread (so they can measure and check if they should time out or
# not...)
threadlocal = threading.local()


class HostTimeoutError(TimeoutError):
    pass


class GlobalTimeoutError(TimeoutError):
    pass


def get_thread_id():
    """Silly util that returns a git-style short-hash id of the thread."""
    return hashlib.md5(str(threading.current_thread().ident).encode("ascii")).hexdigest()[:7]


def sigalrm_handler(threadpool, signal, stackframe):
    logger.warning("Received SIGALRM. Shutting down thread pool.")
    threadpool.shutdown(wait=False, cancel_futures=True)


def on_thread_started(host_id, host_name):
    threadlocal.host_id = host_id
    threadlocal.host_name = host_name


def run_in_threadpool(fn, iterable, fn_args, timeout, executor_kwargs):
    global shutdown, max_global_execution_dt

    max_global_execution_dt = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    threadpool = ThreadPoolExecutor(**executor_kwargs)
    signal.signal(signal.SIGALRM, partial(sigalrm_handler, threadpool))

    def _shutdown_threadpool():
        global shutdown
        shutdown = True
        threadpool.shutdown(cancel_futures=True)

    futures = {threadpool.submit(fn, *fn_args, item) for item in iterable}
    try:
        for future in as_completed(futures, timeout=timeout):
            try:
                yield future.result()
            except Exception:
                logger.exception("Crawler failed!")
    except Exception as e:
        reraised = e
        if isinstance(e, TimeoutError):
            logger.error("The crawl timed out! %s", e)
            reraised = GlobalTimeoutError(str(e))
        elif isinstance(e, KeyboardInterrupt):
            logger.info("Shutting down the thread pool")
        else:
            logger.exception("Unhandled error in the thread pool")
        _shutdown_threadpool()
        raise reraised from e


class ThreadTimeout:
    def __init__(self, max_duration):
        self.max_duration = max_duration
        logger.debug("Host timeout will be %ss", self.max_duration)

    def start(self):
        threadlocal.starttime = time.monotonic()

    def check(self):
        global max_global_execution_dt
        elapsed = self.elapsed()
        if elapsed > self.max_duration:
            raise HostTimeoutError(f"Thread {get_thread_id()} timed out after {elapsed}s")
        if (
            max_global_execution_dt is not None
            and datetime.datetime.now() > max_global_execution_dt
        ):
            raise GlobalTimeoutError(
                f"Maximum run time reached, aborting thread {get_thread_id()} after {elapsed}s"
            )
        if shutdown:
            raise KeyboardInterrupt

    def elapsed(self):
        return time.monotonic() - threadlocal.starttime
