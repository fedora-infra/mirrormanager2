#!/usr/bin/env python

import argparse
import hashlib
import logging
import multiprocessing.pool
import os
import threading
import sys

sys.path.append('..')
import mirrormanager2.lib


logger = logging.getLogger("crawler")


def thread_id():
    """ Silly util that returns a git-style short-hash id of the thread. """
    return hashlib.md5(str(threading.current_thread().ident)).hexdigest()[:7]


def doit(session, options):
    # Get *all* of the mirrors
    hosts = mirrormanager2.lib.get_mirrors(session, private=False)

    # Limit our host list down to only the ones we really want to crawl
    hosts = (
        host for host in hosts if (
            not host.id < options.startid and
            not host.id >= options.stopid and
            not (
                host.admin_active and
                host.user_active and
                host.site.user_active and
                host.site.admin_active) and
            not host.site.private)
    )

    # Then create a threadpool to handle as many at a time as we like
    threadpool = multiprocessing.pool.ThreadPool(processes=options.threads)
    fn = lambda host: worker(session, options, host)
    results = threadpool.map(fn, hosts)
    return results


def setup_logging(debug):
    logging.basicConfig()
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


def main():
    parser = argparse.ArgumentParser(usage=sys.argv[0] + " [options]")
    parser.add_argument(
        "-c", "--config",
        dest="config", default='/etc/mirrormanager/prod.cfg',
        help="Configuration file to use")

    parser.add_argument(
        "--include-private",
        action="store_true", dest="include_private", default=False,
        help="Include hosts marked 'private' in the crawl")

    parser.add_argument(
        "-t", "--threads", type=int, dest="threads", default=10,
        help="max threads to start in parallel")
    parser.add_argument(
        "-l", "--logdir", metavar="DIR",
        dest="logdir", default='crawler',
        help="write individual host logfiles to DIR")
    parser.add_argument(
        "--timeout-minutes", type=int, dest="timeout_minutes", default=120,
        help="per-host timeout, in minutes")
    parser.add_argument(
        "--logfile", metavar="FILE",
        dest="logfile", default='crawler.log',
        help="write logfile to FILE")
    parser.add_argument(
        "--startid", type=int, metavar="ID", dest="startid", default=0,
        help="Start crawling at host ID (default=0)")
    parser.add_argument(
        "--stopid", type=int, metavar="ID",
        dest="stopid", default=sys.maxint,
        help="Stop crawling before host ID (default=maxint)")
    parser.add_argument(
        "--crawler_perhost", metavar="FILE",
        dest="crawler_perhost", default=os.path.abspath('crawler_perhost.py'),
        help="Per-host crawler executable (default=crawler_perhost.py")

    parser.add_argument(
        "--canary", dest="canary", action="store_true", default=False,
        help="fast crawl by only scanning for canary files")

    parser.add_argument(
        "--debug", "-d", dest="debug", action="store_true", default=False,
        help="enable printing of debug-level messages")

    options = parser.parse_args()

    if options.canary:
        raise NotImplementedError("Canary mode is not yet implemented.")

    setup_logging(options.debug)

    d = dict()
    with open(options.config) as config_file:
        exec(compile(config_file.read(), options.config, 'exec'), d)

    session = mirrormanager2.lib.create_session(d['DB_URL'])

    doit(session, options)
    return 0

def worker(session, options, host):
    logger.info("Worker %r looking at host %r" % (thread_id(), host))
    pass

if __name__ == "__main__":
    sys.exit(main())
