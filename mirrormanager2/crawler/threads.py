import hashlib
import logging
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from functools import partial

from .constants import THREAD_TIMEOUT

logger = logging.getLogger(__name__)

# Variable used to coordinate graceful shutdown of all threads
shutdown = False

# This is a "thread local" object that allows us to store the start time of
# each worker thread (so they can measure and check if they should time out or
# not...)
threadlocal = threading.local()


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
    global shutdown
    threadpool = ThreadPoolExecutor(**executor_kwargs)
    signal.signal(signal.SIGALRM, partial(sigalrm_handler, threadpool))
    futures = {threadpool.submit(fn, *fn_args, item) for item in iterable}
    try:
        for future in as_completed(futures, timeout=timeout):
            try:
                yield future.result()
            except Exception:
                logger.exception("Crawler failed!")
    except (TimeoutError, KeyboardInterrupt) as e:
        if isinstance(e, TimeoutError):
            logger.error("The crawl timed out! %s", e)
        elif isinstance(e, KeyboardInterrupt):
            logger.error("Shutting down the thread pool")
        shutdown = True
        threadpool.shutdown(cancel_futures=True)
        raise


class ThreadTimeout:
    def __init__(self, max_duration=THREAD_TIMEOUT):
        self.max_duration = max_duration

    def start(self):
        threadlocal.starttime = time.monotonic()

    def check(self):
        elapsed = self.elapsed()
        if elapsed > (THREAD_TIMEOUT):
            raise TimeoutError(f"Thread {get_thread_id()} timed out after {elapsed}s")
        if shutdown:
            raise KeyboardInterrupt

    def elapsed(self):
        return time.monotonic() - threadlocal.starttime
