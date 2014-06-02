#!/usr/bin/env python

import datetime as dt
import errno
import logging
from optparse import OptionParser
import os
import signal
from subprocess import Popen
import sys
import time
import warnings

sys.path.append('..')
import mirrormanager2.lib
from mirrormanager2 import APP
from mirrormanager2.lib.model import Host
from mirrormanager2.lib.pid import manage_pidfile, remove_pidfile

pidfile='crawler.pid'
options = None
logger = logging.getLogger('crawler')


def total_seconds(td):
    return td.seconds + td.days * 24 * 3600


class ForkingMaster:
    def __init__(self, session, max_children=10):
        self.session = session
        self.active_children = []
        self.max_children = max_children
        self.devnull = open('/dev/null', 'r+')
        self.timings = {}

    def check_timedout_children(self):
        now = dt.datetime.utcnow()
        for child in self.active_children:
            if child.kill_time < now:
                try:
                    # SIGTERM wasn't enough
                    os.kill(child.pid, signal.SIGKILL)
                    logger.info('Killed process %d' % child.pid)
                except: # the process could be gone
                    pass
            else:
                # items lower on this list are newer, no need to check
                break
        return None

    def collect_children(self):
        """Internal routine to wait for died children."""
        options = os.WNOHANG
        while True:
            try:
                pid, status = os.waitpid(-1, options)
            except OSError as e:
                logger.debug(str(e))
                if e.errno == errno.ECHILD:
                    logger.debug(
                        "Got ECHILD.  Number of active children: %d/%d"
                        % (len(self.active_children), self.max_children))
                    return False
                pid = None

            if not pid:
                # no child was ready, see if any should be killed
                self.check_timedout_children()
                return
            # a child should be reaped
            for p in self.active_children:
                if p.pid == pid:
                    self.stop_time(p)
                    logger.debug(
                        "Removing child pid %d, leaving %d active children"
                        % (p.pid, len(self.active_children)-1))
                    self.active_children.remove(p)
        return True

    def process_request(self, command, args, host):
        """Fork a new subprocess to process the request."""
        logger.info("Starting crawler %s: %s" % (host.name, args))
        stderr = open(os.path.join(options.logdir, "%d-stderr.log" % host.id), 'a')

        p = Popen(
            args, executable=command, stdin=self.devnull,
            stdout=self.devnull, stderr=stderr, close_fds=True)
        self.start_time(p, host.id)
        logger.debug("Adding child pid %d" % p.pid)
        self.active_children.append(p)
        logger.debug(
            "Number of active children now: %d" % len(self.active_children))

    def wait_for_available_slot(self):
        logger.debug(
            "Waiting for a slot: Number of active children: %d/%d"
            % (len(self.active_children), self.max_children))
        while len(self.active_children) >= self.max_children:
            self.collect_children()
            time.sleep(1)

    def wait_for_completion(self):
        self.max_children = 0
        while len(self.active_children):
            self.collect_children()
            time.sleep(1)

    def start_time(self, p, hostid):
        now = dt.datetime.utcnow()
        p.kill_time = now + dt.timedelta(
            seconds=(options.timeout_minutes * 60))
        self.timings[p.pid] = dict()
        self.timings[p.pid]['start'] = now
        self.timings[p.pid]['hostid'] = hostid

    def stop_time(self, p):
        self.timings[p.pid]['stop'] = dt.datetime.utcnow()

        diff = self.timings[p.pid]['stop'] - self.timings[p.pid]['start']
        host = mirrormanager2.lib.get_host(
            self.session, self.timings[p.pid]['hostid'])
        logger.info(
            'Host %s (id=%s) crawl time %s'
            % (host.name, host.id, str(diff)))

        try:
            seconds = int(diff.total_seconds())
        except AttributeError: # python < 2.7
            seconds = total_seconds(diff)
        host.last_crawl_duration = seconds
        del self.timings[p.pid]


def doit(session):
    master = ForkingMaster(session=session, max_children=options.threads)
    commonargs = [ options.crawler_perhost, '-c', options.config]
    if options.canary:
        commonargs.append('--canary')

    hosts = mirrormanager2.lib.get_mirrors(session, private=False)
    numhosts = len(hosts)
    i = 0
    for host in hosts:
        i += 1
        try:
            if host.id < options.startid: continue
            if host.id >= options.stopid: continue
            master.wait_for_available_slot()

            if not (host.admin_active and host.user_active
                    and host.site.user_active and host.site.admin_active):
                continue
            if host.site.private:
                continue

            hostargs = []
            hostargs.extend(['--hostid', str(host.id)])
            logfilename = os.path.join(options.logdir, str(host.id) + '.log')
            hostargs.extend(['--logfile', logfilename])
            args = commonargs + hostargs
            logger.debug(
                'starting crawler for host %s (id=%d) %d/%d'
                % (host.name, host.id, i, numhosts))
            master.process_request(options.crawler_perhost, args, host)
        except AssertionError:
            # someone deleted our host while we were looking at it
            continue

    master.wait_for_completion()


def setup_logger(debug):
    formatter = logging.Formatter(fmt="%(asctime)s %(message)s")
    formatter.converter = time.gmtime
    handler = logging.handlers.WatchedFileHandler(options.logfile, "a+b")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


def main():
    global options
    if manage_pidfile(pidfile):
        print "another instance is running, try again later."
        return 1

    parser = OptionParser(usage=sys.argv[0] + " [options]")
    parser.add_option(
        "-c", "--config",
        dest="config", default='/etc/mirrormanager/prod.cfg',
        help="Configuration file to use")

    parser.add_option(
        "--include-private",
        action="store_true", dest="include_private", default=False,
        help="Include hosts marked 'private' in the crawl")

    parser.add_option(
        "-t", "--threads", type="int", dest="threads", default=10,
        help="max threads to start in parallel")
    parser.add_option(
        "-l", "--logdir", type="string", metavar="DIR",
        dest="logdir", default='crawler',
        help="write individual host logfiles to DIR")
    parser.add_option(
        "--timeout-minutes", type="int", dest="timeout_minutes", default=120,
        help="per-host timeout, in minutes")
    parser.add_option(
        "--logfile", type="string", metavar="FILE",
        dest="logfile", default='crawler.log',
        help="write logfile to FILE")
    parser.add_option(
        "--startid", type="int", metavar="ID", dest="startid", default=0,
        help="Start crawling at host ID (default=0)")
    parser.add_option(
        "--stopid", type="int", metavar="ID",
        dest="stopid", default=sys.maxint,
        help="Stop crawling before host ID (default=maxint)")
    parser.add_option(
        "--crawler_perhost", type="string", metavar="FILE",
        dest="crawler_perhost", default='/home/pierrey/repos/gitrepo/mirrormanager2/utility/crawler_perhost.py',
        help="Per-host crawler executable (default=crawler_perhost.py")

    parser.add_option(
        "--canary", dest="canary", action="store_true", default=False,
        help="fast crawl by only scanning for canary files")

    parser.add_option(
        "--debug", "-d", dest="debug", action="store_true", default=False,
        help="enable printing of debug-level messages")

    (options, args) = parser.parse_args()

    global logger
    logger = setup_logger(options.debug)

    d = dict()
    with open(options.config) as config_file:
        exec(compile(config_file.read(), options.config, 'exec'), d)

    session = mirrormanager2.lib.create_session(d['DB_URL'])

    doit(session)
    remove_pidfile(pidfile)
    return 0

if __name__ == "__main__":
    sys.exit(main())
