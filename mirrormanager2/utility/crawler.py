#!/usr/bin/env python3

import csv
import datetime
import ftplib
import gc
import hashlib
import logging
import multiprocessing.pool
import os
import signal
import smtplib
import socket
import sys
import threading
import time
from ftplib import FTP
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from urllib.parse import urlparse
from urllib.request import urlopen

import click
import geoip2.database

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import HostCategoryDir
from mirrormanager2.lib.sync import run_rsync

from .common import read_config

logger = logging.getLogger("crawler")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
master_formatter = (
    "%(levelname)s:%(name)s:%(hosts)s:%(threads)s:%(hostid)s:%(hostname)s:%(message)s"
)
current_host = 0
all_hosts = 0
threads = 0
threads_active = 0
hosts_failed = 0
check_start = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())

# This is the global timeout variable, so that it can be
# decreased by the signal handler and thus change in all threads.
timeout = 120

# Variable used to coordinate graceful shutdown of all threads
shutdown = False

# our own private copy of country_continents to be edited
country_continents = {}
gi = geoip2.database.Reader("/usr/share/GeoIP/GeoLite2-Country.mmdb")
# hard coded list of continents; let's hope this does not change all the time
# this is according to GeoIP
continents = ["AF", "AN", "AS", "EU", "NA", "OC", "SA", "--"]

# This is a "thread local" object that allows us to store the start time of
# each worker thread (so they can measure and check if they should time out or
# not...)
threadlocal = threading.local()


# To insert information about the number of hosts and threads in each master
# log message this filter is necessary
class MasterFilter(logging.Filter):
    def filter(self, record):
        record.hosts = "Hosts(%d/%d)" % (current_host, all_hosts)
        record.threads = "Threads(%d/%d)" % (threads_active, threads)
        try:
            record.hostid = threadlocal.hostid
            record.hostname = threadlocal.hostname
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


def sigalrm_handler(signal, stackframe):
    global timeout
    global shutdown
    logger.warning("Received SIGALRM. Setting global timeout to -1.")
    timeout = -1
    shutdown = True


def thread_id():
    """Silly util that returns a git-style short-hash id of the thread."""
    return hashlib.md5(str(threading.current_thread().ident)).hexdigest()[:7]


# Add the information from the country_continent_redirect table to
# country_continents information from GeoIP
def handle_country_continent_redirect(session):
    country_continent_csv = "/usr/share/mirrormanager2/country_continent.csv"
    new_country_continents = {}
    with open(country_continent_csv) as infile:
        reader = csv.reader(infile)
        new_country_continents = {rows[0]: rows[1] for rows in reader}
    for c in mirrormanager2.lib.get_country_continent_redirect(session):
        new_country_continents[c.country] = c.continent
    global country_continents
    country_continents = new_country_continents


def notify(options, topic, msg):
    if not options["fedmsg"]:
        return

    mirrormanager2.lib.notifications.fedmsg_publish(
        f"mirrormanager.crawler.{topic}",
        msg,
    )


def doit(options, config):
    global all_hosts
    global threads
    global timeout
    global shutdown
    global continents

    shutdown_timer = 0
    # number of minutes to wait if a signal is received to shutdown the crawler
    SHUTDOWN_TIMEOUT = 5

    # Fill continent list
    if options["continents"]:
        if any(item.startswith("^") for item in options["continents"]):
            for item in options["continents"]:
                if item.startswith("^"):
                    try:
                        continents.remove(item[1:].upper())
                    except ValueError:
                        # A continent was specified which is not
                        # in the continents list. Just ignore it.
                        msg = "Ignoring unknown continent: "
                        msg += item[1:].upper()
                        logger.warning(msg)
                        msg = "Not in the list of known continents. "
                        msg += "%r"
                        logger.warning(msg % continents)
                        pass
        else:
            continents = options["continents"]

        continents = [x.upper() for x in continents]

    db_manager = get_db_manager(config)
    session = db_manager.Session()

    # load country_continent mapping
    handle_country_continent_redirect(session)

    # Get *all* of the mirrors
    hosts = mirrormanager2.lib.get_mirrors(
        session,
        private=False,
        order_by_crawl_duration=True,
        admin_active=True,
        user_active=True,
        site_private=False,
        site_user_active=True,
        site_admin_active=True,
    )

    # Get a list of host names for fedmsg
    host_names = [
        host.name
        for host in hosts
        if (not host.id < options["startid"] and not host.id >= options["stopid"])
    ]

    # Limit our host list down to only the ones we really want to crawl
    hosts = [
        host.id
        for host in hosts
        if (not host.id < options["startid"] and not host.id >= options["stopid"])
    ]

    session.close()
    all_hosts = len(hosts)

    # And then, for debugging, only do one host
    # hosts = [hosts.next()]

    hostlist = [dict(id=id, host=host) for id, host in zip(hosts, host_names)]
    msg = dict(hosts=hostlist)
    msg["options"] = options
    notify(options, "start", msg)

    # Before we do work, chdir to /var/tmp/.  mirrormanager1 did this and I'm
    # not totally sure why...
    os.chdir("/var/tmp")

    signal.signal(signal.SIGALRM, sigalrm_handler)
    # Then create a threadpool to handle as many at a time as we like
    threadpool = multiprocessing.pool.ThreadPool(processes=threads)

    def fn(host_id):
        return worker(options, config, host_id)

    # Here's the big operation
    result = threadpool.map_async(fn, hosts)

    while not result.ready():
        time.sleep(1)
        if shutdown:
            # Being here means that the signal handler was called and the
            # timeout was decreased to -1. Not starting any new workers.
            threadpool.close()
            # Wait for SHUTDOWN_TIMEOUT minutes for all threads to shutdown
            shutdown_timer = time.time()
            shutdown = False
        if shutdown_timer:
            delta = time.time() - shutdown_timer
            if delta > SHUTDOWN_TIMEOUT * 60:
                # Time out for graceful shutdown is over.
                # Let's terminate all threads.
                logger.warning("About to terminate all threads.")
                threadpool.terminate()
                logger.warning("About to terminate all threads. Done.")
                break

    try:
        logger.info("Retrieving results.")
        # Only waiting 60 seconds for the results.
        # We already waited SHUTDOWN_TIMEOUT minutes above.
        # It would be nice to get the return codes of the successful crawls.
        return_codes = result.get(60)
    except multiprocessing.TimeoutError:
        # There are threads which did not finish during the timeout.
        # Put bogus results in return_codes.
        logger.info("Retrieving results failed. Inventing return codes.")
        return_codes = [42] * len(hosts)

    # Put a bow on the results for fedmsg
    results = [
        dict(rc=rc, host=host, id=id) for rc, host, id in zip(return_codes, host_names, hosts)
    ]

    notify(options, "complete", dict(results=results))

    if options["canary"]:
        mode = " in canary mode"
    elif options["repodata"]:
        mode = " in repodata mode"
    else:
        mode = ""

    logger.info("%d of %d hosts failed%s" % (hosts_failed, current_host, mode))
    return results


def setup_logging(debug):
    logging.basicConfig(format=master_formatter)
    f = MasterFilter()
    logger.addFilter(f)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


def set_global(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    globals()[param] = value


@click.command()
@click.option(
    "-c",
    "--config",
    default="/etc/mirrormanager/mirrormanager2.cfg",
    help="Configuration file to use",
)
@click.option(
    "--include-private",
    is_flag=True,
    default=False,
    help="Include hosts marked 'private' in the crawl",
)
@click.option(
    "-t",
    "--threads",
    type=int,
    default=10,
    help="max threads to start in parallel",
    expose_value=False,
    callback=set_global,
)
@click.option(
    "--timeout-minutes",
    "timeout",
    type=int,
    default=120,
    help="per-host timeout, in minutes",
    expose_value=False,
    callback=set_global,
)
@click.option(
    "--startid",
    type=int,
    metavar="ID",
    default=0,
    help="Start crawling at host ID (default=0)",
)
@click.option(
    "--stopid",
    type=int,
    metavar="ID",
    default=sys.maxint,
    help="Stop crawling before host ID (default=maxint)",
)
@click.option(
    "--category",
    "categories",
    multiple=True,
    help="Category to scan (default=all), can be repeated",
)
@click.option(
    "--disable-fedmsg",
    "fedmsg",
    is_flag=True,
    default=True,
    help="Disable fedora-messaging notifications at the beginning and end of crawl",
)
@click.option(
    "--canary",
    is_flag=True,
    default=False,
    help="Fast crawl by only checking if mirror can be reached",
)
@click.option(
    "--repodata",
    is_flag=True,
    default=False,
    help="Fast crawl by only checking if the repodata is up to date",
)
@click.option(
    "--continent",
    "continents",
    multiple=True,
    help="Limit crawling by continent. Exclude by prefixing with'^'",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    default=False,
    help="enable printing of debug-level messages",
)
@click.option(
    "-p",
    "--propagation",
    is_flag=True,
    default=False,
    help="Print out information about repomd.xml propagation "
    "Defaults to development/rawhide/x86_64/os/repodata "
    "Only the category 'Fedora Linux' is supported",
)
@click.option(
    "--proppath",
    metavar="PATH",
    default="development/rawhide/x86_64/os/repodata",
    help="Use another path for propgation check  "
    "Defaults to development/rawhide/x86_64/os/repodata",
)
@click.pass_context
def main(
    ctx,
    config,
    debug,
):
    starttime = time.time()
    setup_logging(debug)
    config = read_config(config)
    doit(ctx.params, config)
    logger.info("Crawler finished after %d seconds" % (time.time() - starttime))
    return 0


################################################
# overrides for http.client because we're
# handling keepalives ourself
################################################
class myHTTPResponse(HTTPResponse):
    def begin(self):
        HTTPResponse.begin(self)
        self.will_close = False

    def isclosed(self):
        """This is a hack, because otherwise httplib will fail getresponse()"""
        return True

    def keepalive_ok(self):
        # HTTP/1.1 connections stay open until closed
        if self.version == 11:
            ka = self.msg.getheader("connection")
            if ka and "close" in ka.lower():
                return False
            else:
                return True

        # other HTTP connections may have a connection: keep-alive header
        ka = self.msg.getheader("connection")
        if ka and "keep-alive" in ka.lower():
            return True

        try:
            ka = self.msg.getheader("keep-alive")
            if ka is not None:
                maxidx = ka.index("max=")
                maxval = ka[maxidx + 4 :]
                if maxval == "1":
                    return False
                return True
            else:
                ka = self.msg.getheader("connection")
                if ka and "keep-alive" in ka.lower():
                    return True
                return False
        except Exception:
            return False
        return False


class myHTTPConnection(HTTPConnection):
    response_class = myHTTPResponse

    def end_request(self):
        self.__response = None


class myHTTPSConnection(HTTPSConnection):
    response_class = myHTTPResponse

    def end_request(self):
        self.__response = None


################################################
# the magic begins


def timeout_check():
    global timeout
    delta = time.time() - threadlocal.starttime
    if delta > (timeout * 60):
        raise TimeoutException("Timed out after %rs" % delta)


class hostState:
    def __init__(self, http_debuglevel=0, ftp_debuglevel=0, timeout_minutes=120):
        self.httpconn = {}
        self.httpsconn = {}
        self.ftpconn = {}
        self.http_debuglevel = http_debuglevel
        self.ftp_debuglevel = ftp_debuglevel
        self.ftp_dir_results = None
        self.keepalives_available = False
        # ftplib and httplib take the timeout in seconds
        self.timeout = timeout_minutes * 60

    def get_connection(self, url):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        if scheme == "ftp":
            if netloc in self.ftpconn:
                return self.ftpconn[netloc]
        elif scheme == "http":
            if netloc in self.httpconn:
                return self.httpconn[netloc]
        elif scheme == "https":
            if netloc in self.httpsconn:
                return self.httspconn[netloc]
        return None

    def open_http(self, url):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        if scheme == "http":
            if netloc not in self.httpconn:
                self.httpconn[netloc] = myHTTPConnection(netloc, timeout=self.timeout)
                self.httpconn[netloc].set_debuglevel(self.http_debuglevel)
            return self.httpconn[netloc]

        elif scheme == "https":
            if netloc not in self.httpsconn:
                self.httpsconn[netloc] = myHTTPSConnection(netloc, timeout=self.timeout)
                self.httpsconn[netloc].set_debuglevel(self.http_debuglevel)
            return self.httpsconn[netloc]

    def _open_ftp(self, netloc):
        if netloc not in self.ftpconn:
            self.ftpconn[netloc] = FTP(netloc, timeout=self.timeout)
            self.ftpconn[netloc].set_debuglevel(self.ftp_debuglevel)
            self.ftpconn[netloc].login()

    def check_ftp_dir_callback(self, line):
        if self.ftp_debuglevel > 0:
            logger.info(line)
        self.ftp_dir_results.append(line)

    def ftp_dir(self, url):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        self._open_ftp(netloc)
        c = self.ftpconn[netloc]
        self.ftp_dir_results = []
        c.dir(path, self.check_ftp_dir_callback)

    def close_http(self, url):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        if scheme == "http":
            if netloc in self.httpconn:
                self.httpconn[netloc].close()
                del self.httpconn[netloc]

        elif scheme == "https":
            if netloc in self.httpsconn:
                self.httpsconn[netloc].close()
                del self.httpsconn[netloc]

    def close_ftp(self, url):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        if netloc in self.ftpconn:
            try:
                self.ftpconn[netloc].quit()
            except Exception:
                pass
            del self.ftpconn[netloc]

    def close(self):
        for c in self.httpconn.keys():
            self.close_http(c)

        for c in self.httpsconn.keys():
            self.close_http(c)

        for c in self.ftpconn.keys():
            self.close_ftp(c)


class TryLater(Exception):
    pass


class ForbiddenExpected(Exception):
    pass


class TimeoutException(Exception):
    pass


class WrongContinent(Exception):
    pass


class HTTPUnknown(Exception):
    pass


class HTTP500(Exception):
    pass


def get_ftp_dir(hoststate, url, readable, i=0):
    if i > 1:
        raise TryLater()

    try:
        hoststate.ftp_dir(url)
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
                raise ForbiddenExpected() from e
        # Returned by ftp2.surplux.net when cannot log in due to connection
        # restrictions
        if str(e).startswith("530"):
            hoststate.close_ftp(url)
            return get_ftp_dir(hoststate, url, readable, i + 1)
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
        hoststate.close_ftp(url)
        return get_ftp_dir(hoststate, url, readable, i + 1)

    return hoststate.ftp_dir_results


def check_ftp_file(hoststate, url, filedata, readable):
    if url.endswith("/"):
        url = url[:-1]
    try:
        results = get_ftp_dir(hoststate, url, readable)
    except TryLater:
        raise
    except ForbiddenExpected:
        return None
    if results is None:
        return None
    if len(results) == 1:
        line = results[0].split()
        # For the basic check in check_for_base_dir() it is only
        # relevant if the directory exists or not. Therefore
        # passing None as filedata[]. This needs to be handled here.
        if filedata is None:
            # The file/directory seems to exist
            return True
        if float(line[4]) == float(filedata["size"]):
            return True
    return False


def check_url(hoststate, url, filedata, recursion, readable):
    if url.startswith(("http:", "https:")):
        return check_head(hoststate, url, filedata, recursion, readable)
    elif url.startswith("ftp:"):
        return check_ftp_file(hoststate, url, filedata, readable)


def handle_redirect(hoststate, url, location, filedata, recursion, readable):
    if recursion > 10:
        raise HTTPUnknown()
    if location.startswith("/"):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        location = f"{scheme}:{netloc}{location}"
    return check_url(hoststate, location, filedata, recursion + 1, readable)


def check_head(hoststate, url, filedata, recursion, readable, retry=0):
    """Returns tuple:
    True - URL exists
    False - URL doesn't exist
    None - we don't know
    """

    try:
        conn = hoststate.open_http(url)
    except Exception:
        return None

    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    reqpath = path
    if len(query) > 0:
        reqpath += "?%s" % query
    if len(fragment) > 0:
        reqpath += "#%s" % fragment

    r = None
    try:
        conn.request(
            "HEAD",
            reqpath,
            headers={
                "Connection": "Keep-Alive",
                "Pragma": "no-cache",
                "User-Agent": "mirrormanager-crawler/0.1 (+https://"
                "github.com/fedora-infra/mirrormanager2/)",
            },
        )
        r = conn.getresponse()
        status = r.status
    except Exception as e:
        if retry == 0:
            # If the above attempt to connect to the mirror fails, the crawler
            # will retry once. One possible reason for a connection failure is
            # that the connection, which is kept open to leverage keep-alive,
            # has been closed by the remote end. Therefore we are closing
            # the connection and are restarting the whole operation.
            hoststate.close_http(url)
            return check_head(hoststate, url, filedata, recursion, readable, retry=1)
        else:
            raise HTTPUnknown() from e

    conn.end_request()
    keepalive_ok = r.keepalive_ok()
    if keepalive_ok:
        hoststate.keepalives_available = True
    if not keepalive_ok:
        hoststate.close_http(url)

    content_length = r.getheader("Content-Length")
    # last_modified  = r.getheader('Last-Modified')

    if status >= 200 and status < 300:
        # lighttpd returns a Content-Length for directories
        # apache and nginx do not
        # For the basic check in check_for_base_dir() it is only
        # relevant if the directory exists or not. Therefore
        # passing None as filedata[]. This needs to be handled here.
        if filedata is None:
            # The file/directory seems to exist
            return True
        # fixme should check last_modified too
        if float(filedata["size"]) == float(content_length) or content_length is None:
            # handle no content-length header, streaming/chunked return
            # or zero-length file
            return True
        else:
            return False
    if status >= 300 and status < 400:
        return handle_redirect(
            hoststate, url, r.getheader("Location"), filedata, recursion, readable
        )
    elif status >= 400 and status < 500:
        if status == 403:  # forbidden
            # may be a hidden dir still
            if readable:
                return False
            else:
                raise ForbiddenExpected()
        elif status == 404 or status == 410:  # not found / gone
            return False
        # we don't know
        return None
    elif status >= 500:
        raise HTTP500()

    logger.info("status = %s" % status)
    raise HTTPUnknown()


def report_stats(stats):
    msg = "Crawl duration: %d seconds" % stats["duration"]
    logger.info(msg)
    msg = "Total directories: %d" % stats["numkeys"]
    logger.info(msg)
    msg = "Unreadable directories: %d" % stats["unreadable"]
    logger.info(msg)
    msg = "Changed to up2date: %d" % stats["up2date"]
    logger.info(msg)
    msg = "Changed to not up2date: %d" % stats["not_up2date"]
    logger.info(msg)
    msg = "Unchanged: %d" % stats["unchanged"]
    logger.info(msg)
    msg = "Unknown disposition: %d" % stats["unknown"]
    logger.info(msg)
    msg = "New HostCategoryDirs created: %d" % stats["newdir"]
    logger.info(msg)
    msg = (
        "HostCategoryDirs now deleted on the master, marked not "
        "up2date: %d" % stats["deleted_on_master"]
    )
    logger.info(msg)


def sync_hcds(session, host, host_category_dirs, options):
    stats = dict(
        up2date=0,
        not_up2date=0,
        unchanged=0,
        unreadable=0,
        unknown=0,
        newdir=0,
        deleted_on_master=0,
        duration=0,
    )
    current_hcds = {}
    stats["duration"] = time.time() - threadlocal.starttime
    keys = host_category_dirs.keys()
    keys = sorted(keys, key=lambda t: t[1].name)
    stats["numkeys"] = len(keys)
    for hc, d in keys:
        up2date = host_category_dirs[(hc, d)]
        if up2date is None:
            stats["unknown"] += 1
            continue

        topname = hc.category.topdir.name
        toplen = len(topname)
        if d.name.startswith("/"):
            toplen += 1
        path = d.name[toplen:]

        hcd = mirrormanager2.lib.get_hostcategorydir_by_hostcategoryid_and_path(
            session, host_category_id=hc.id, path=path
        )
        if len(hcd) > 0:
            hcd = hcd[0]
        else:
            # don't create HCDs for directories which aren't up2date on the
            # mirror chances are the mirror is excluding that directory
            if not up2date:
                continue
            hcd = HostCategoryDir(host_category_id=hc.id, path=path, directory_id=d.id)
            stats["newdir"] += 1

        if hcd.directory is None:
            hcd.directory = d
        if hcd.up2date != up2date:
            hcd.up2date = up2date
            session.add(hcd)
            if up2date is False:
                logger.info("Directory %s is not up-to-date on this host." % d.name)
                stats["not_up2date"] += 1
            else:
                logger.info(d.name)
                stats["up2date"] += 1
        else:
            stats["unchanged"] += 1

        current_hcds[hcd] = True

    # In repodata mode we only want to update the files actually scanned.
    # Do not mark files which have not been scanned as not being up to date.
    if not options["repodata"]:
        # now-historical HostCategoryDirs are not up2date
        # we wait for a cascading Directory delete to delete this
        host_categories_to_scan = select_host_categories_to_scan(session, options, host)
        for hc in host_categories_to_scan:
            for hcd in list(hc.directories):
                if hcd.directory is not None and not hcd.directory.readable:
                    stats["unreadable"] += 1
                    continue
                if hcd not in current_hcds:
                    if hcd.up2date is not False:
                        hcd.up2date = False
                        session.add(hcd)
                        stats["deleted_on_master"] += 1
    session.commit()
    report_stats(stats)
    del current_hcds
    del stats


def method_pref(urls, prev=""):
    """return which of the hosts connection method should be used
    rsync > http(s) > ftp"""
    pref = None
    for u in urls:
        if prev.startswith("rsync:"):
            break
        if u.startswith("rsync:"):
            return u
    for u in urls:
        if u.startswith(("http:", "https:")):
            pref = u
            break
    if pref is None:
        for u in urls:
            if u.startswith("ftp:"):
                pref = u
                break
    logger.info("Crawling with URL %s" % pref)
    return pref


def parent(session, directory):
    parentDir = None
    splitpath = directory.name.split("/")
    if len(splitpath[:-1]) > 0:
        parentPath = "/".join(splitpath[:-1])
        parentDir = mirrormanager2.lib.get_directory_by_name(session, parentPath)
    return parentDir


def add_parents(session, host_category_dirs, hc, d):
    parentDir = parent(session, d)
    if parentDir is not None:
        if (hc, parentDir) not in host_category_dirs:
            host_category_dirs[(hc, parentDir)] = None
        if parentDir != hc.category.topdir:  # stop at top of the category
            return add_parents(session, host_category_dirs, hc, parentDir)

    return host_category_dirs


def compare_sha256(d, filename, graburl):
    """looks for a FileDetails object that matches the given URL"""
    found = False
    s = urlopen(graburl)
    sha256 = hashlib.sha256(s.read()).hexdigest()
    for fd in list(d.fileDetails):
        if fd.filename == filename and fd.sha256 is not None:
            if fd.sha256 == sha256:
                found = True
                break
    return found


def try_per_file(d, hoststate, url):
    if d.files is None:
        return None
    exists = None
    # d.files is a dict which contains the last (maybe 10) files
    # of the current directory. umdl copies the pickled dict
    # into the database. It is either a dict or nothing.
    if not isinstance(d.files, dict):
        return None
    for filename in d.files:
        # Check if maximum crawl time for this host has been reached
        timeout_check()
        exists = None
        graburl = f"{url}/{filename}"
        try:
            exists = check_url(hoststate, graburl, d.files[filename], 0, d.readable)
            if exists is False:
                return False
        except TryLater:
            raise
        except ForbiddenExpected:
            return None
        except ftplib.all_errors:
            hoststate.close_ftp(url)
            return None
        except Exception:
            return None

        if filename == "repomd.xml":
            try:
                exists = compare_sha256(d, filename, graburl)
            except Exception:
                pass
            if exists is False:
                return False

    if exists is None:
        return None

    return True


def try_per_category(
    session, trydirs, url, host_category_dirs, hc, host, categoryPrefixLen, config
):
    """In addition to the crawls using http and ftp, this rsync crawl
    scans the complete category with one connection instead perdir (ftp)
    or perfile(http)."""

    if not url.startswith("rsync"):
        return False

    # rsync URL available, let's use it; it requires only one network
    # connection instead of multiples like with http and ftp
    rsync = {}
    if not url.endswith("/"):
        url += "/"

    timeout_check()

    # Get remaining time this crawl thread has
    remaining = (timeout * 60) - (time.time() - threadlocal.starttime)
    # Give the rsync process 90% of the remaining time to finish
    # the listing of the available files. 90% could already be too
    # much as updating the status of all scanned directories in the
    # database usually takes quite some time. But there are more
    # timeout checks all over the crawler code to make sure we are
    # not over the timeout.
    local_timeout = int(remaining * 0.9)

    rsync_start_time = datetime.datetime.utcnow()
    params = config.get("CRAWLER_RSYNC_PARAMETERS", "--no-motd")
    try:
        result, listing = run_rsync(url, params, logger, local_timeout)
    except Exception:
        logger.exception("Failed to run rsync.", exc_info=True)
        return False
    rsync_stop_time = datetime.datetime.utcnow()
    msg = "rsync time: %s" % str(rsync_stop_time - rsync_start_time)
    logger.info(msg)
    if result == 10:
        # no rsync content, fail!
        logger.warning(
            "Connection to host %s Refused.  Please check that the URL is "
            "correct and that the host has an rsync module still available." % host.name
        )
        return False
    if result > 0:
        logger.info("rsync returned exit code %d" % result)

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
    if len(rsync) == 0:
        # no rsync content, fail!
        return False
    # for all directories in this category
    for d in trydirs:
        # Check if maximum crawl time for this host has been reached
        timeout_check()

        # ignore unreadable directories - we can't really know about them
        if not d.readable:
            host_category_dirs[(hc, d)] = None
            continue

        all_files = True
        # the rsync listing is missing the category part of the url
        # remove if from the ones we are comparing it with
        name = d.name[categoryPrefixLen:]
        # d.files is a dict which contains the last (maybe 10) files
        # of the current directory. umdl copies the pickled dict
        # into the database. It is either a dict or nothing.
        if not isinstance(d.files, dict):
            return False
        for filename in sorted(d.files):
            if len(name) == 0:
                key = filename
            else:
                key = os.path.join(name, filename)
            try:
                logger.debug("trying with key %s" % key)
                if float(rsync[key]["size"]) != float(d.files[filename]["size"]) and not rsync[key][
                    "mode"
                ].startswith("l"):
                    # ignore symlink size differences
                    logger.debug(
                        "rsync: file size mismatch {} {} != {}\n".format(
                            filename, d.files[filename]["size"], rsync[key]["size"]
                        )
                    )
                    all_files = False
                    break
            except ValueError:  # one of the conversion to float() failed
                msg = "Invalid size value for file %s\n" % key
                logger.debug(msg)
                all_files = False
                break
            except KeyError:  # file is not in the rsync listing
                msg = "Missing remote file %s\n" % key
                logger.debug(msg)
                all_files = False
                break
            except Exception:  # something else went wrong
                exception_msg = "Exception caught in try_per_category()\n"
                logger.exception(exception_msg)
                all_files = False
                break

        if all_files is False:
            host_category_dirs[(hc, d)] = False
        else:
            host_category_dirs[(hc, d)] = True
            host_category_dirs = add_parents(session, host_category_dirs, hc, d)

    del rsync

    if len(host_category_dirs) > 0:
        return True

    mark_not_up2date(
        session,
        config,
        None,
        host,
        "No host category directories found.  " "Check that your Host Category URLs are correct.",
    )
    return False


def try_per_dir(d, hoststate, url):
    if d.files is None:
        return None
    if not url.startswith("ftp"):
        return None
    results = {}
    if not url.endswith("/"):
        url += "/"
    listing = get_ftp_dir(hoststate, url, d.readable)
    if listing is None:
        return None

    if len(listing) == 0:
        return False

    # Check if maximum crawl time for this host has been reached
    timeout_check()

    for line in listing:
        if line.startswith(
            "total"
        ):  # some servers first include a line starting with the word 'total' that we can ignore
            continue
        fields = line.split()
        try:
            results[fields[8]] = {"size": fields[4]}
        except IndexError:  # line doesn't have 8 fields, it's not a dir line
            pass

    # d.files is a dict which contains the last (maybe 10) files
    # of the current directory. umdl copies the pickled dict
    # into the database. It is either a dict or nothing.
    if not isinstance(d.files, dict):
        return False
    for filename in d.files:
        try:
            if float(results[filename]["size"]) != float(d.files[filename]["size"]):
                return False
        except Exception:
            return False
    return True


def send_email(config, host, report_str, exc):
    if not config.get("CRAWLER_SEND_EMAIL", False):
        return

    SMTP_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
    msg = """From: {}
To: {}
Subject: {} MirrorManager crawler report
Date: {}

""".format(
        config.get("EMAIL_FROM"),
        config.get("ADMIN_EMAIL"),
        host.name,
        time.strftime(SMTP_DATE_FORMAT),
    )

    msg += report_str + "\n"
    msg += "Log can be found at {}/{}.log\n".format(config.get("crawler.logdir"), str(host.id))
    if exc is not None:
        msg += f"Exception info: type {exc[0]}; value {exc[1]}\n"
        msg += str(exc[2])
    try:
        smtp = smtplib.SMTP(config.get("SMTP_SERVER"))

        username = config.get("SMTP_USERNAME")
        password = config.get("SMTP_PASSWORD")

        if username and password:
            smtp.login(username, password)

        smtp.sendmail(config.get("SMTP_SERVER"), config.get("ADMIN_EMAIL"), msg)
    except Exception:
        logger.exception("Error sending email")
        logger.debug("Email message follows:")
        logger.debug(msg)

    try:
        smtp.quit()
    except Exception:
        pass


def mark_not_up2date(session, config, exc, host, reason="Unknown"):
    """This function marks a complete host as not being up to date.
    It usually is called if the scan of a single category has failed.
    This is something the crawler does at multiple places: Failure
    in the scan of a single category disables the complete host."""
    # Watch out: set_not_up2date(session) is commiting all changes
    # in this thread to the database
    host.set_not_up2date(session)
    msg = f"Host {host.id} marked not up2date: {reason}"
    logger.warning(msg)
    if exc is not None:
        logger.debug(f"{exc[0]} {exc[1]} {exc[2]}")
    send_email(config, host, msg, exc)


def select_host_categories_to_scan(session, options, host):
    result = []
    if options["categories"]:
        for category in options["categories"]:
            hc = mirrormanager2.lib.get_host_category_by_hostid_category(
                session, host_id=host.id, category=category
            )
            for entry in hc:
                result.append(entry)
    else:
        result = list(host.categories)
    return result


def check_for_base_dir(hoststate, urls):
    """Check if at least one of the given URL exists on the remote host.
    This is used to detect mirrors which have completely dropped our content.
    This is only looking at http and ftp URLs as those URLs are actually
    relevant for normal access. If both tests fail the mirror will be marked
    as failed during crawl.
    """
    exists = False
    for u in urls:
        if not u.endswith("/"):
            u += "/"
        if u.startswith(("http:", "https:")):
            try:
                exists = check_head(hoststate, u, None, False, True)
            except Exception:
                exists = False
            if not exists:
                logger.warning("Base URL %s does not exist." % u)
                continue
            # The base http URL seems to work. Good!
            return True
        if u.startswith("ftp:"):
            try:
                exists = get_ftp_dir(hoststate, u, True)
            except TryLater:
                # Some temporary difficulties on the mirror
                exists = False
            # exists is an empty list if that directory does not exist
            if not exists:
                logger.warning("Base URL %s does not exist." % u)
                continue
            # The base ftp URL seems to work. Good!
            return True

    # Reaching this point means that no functional http/ftp has been
    # found. This means that the mirror will not work for normal http
    # and ftp users.
    return False


def check_continent(categoryUrl):
    # Before the first network access to the mirror let's
    # check if continent mode is enabled and verfiy if
    # the mirror is on the target continent.
    # The continent check takes the first URL of the first category
    # for the decision on which continent the mirror is.
    try:
        hostname = urlparse.urlsplit(categoryUrl)[1]
    except Exception:
        # Not being able the split the URL is strange.
        # Something is broken. '5' is the start for auto-disablement
        return 5

    # The function urlsplit() does not remove ':' in case someone
    # specified a port. Only look at the first element before ':'
    hostname = hostname.split(":")[0]

    try:
        hostname = socket.gethostbyname(hostname)
    except Exception:
        # Name resolution failed. Returning '5' as this means
        # that the base URL is broken.
        return 5

    country = gi.country(hostname).country.iso_code
    if not country:
        # For hosts with no country in the GeoIP database
        # the default is 'US' as that is where most of
        # Fedora infrastructure systems are running
        country = "US"
    if country_continents[country] in continents:
        return 0
    # And another return value. '8' is used for mirrors on
    # the wrong continent. The crawl should not be listed in
    # the database at all.
    return 8


def check_propagation(session, catname, topdir, host_category_urls, path):
    # Print out information about the repomd.xml status
    base = os.path.join(topdir, path)
    url = None
    for u in host_category_urls:
        if not u.endswith("/"):
            u += "/"
        if u.startswith("http:"):
            url = u
    if not url:
        return 9
    d = mirrormanager2.lib.get_directory_by_name(session, base)
    if d is None:
        return 9
    fd = mirrormanager2.lib.get_file_detail(session, "repomd.xml", d.id, reverse=True)
    url += path
    url += "/repomd.xml"
    import requests

    ses = requests.Session()
    try:
        contents = ses.get(url, timeout=30)
    except requests.exceptions.ConnectionError:
        logger.info(
            "URL::{}::SHA256::{}::{}::{}::503::{}".format(
                url, "NOSUM", check_start, fd.sha256, path
            )
        )
        return 9
    has = hashlib.sha256()
    has.update(contents.content)
    csum = has.hexdigest()
    logger.info(
        f"URL::{url}::SHA256::{csum}::{check_start}::{fd.sha256}::{contents.status_code}::{path}"
    )
    return 9


def per_host(session, host, options, config):
    """This function scans all categories a host has defined.
    If a RSYNC URL is available it tries to scan the host requiring
    only single network connection. If this is not possible or fails
    it tries to scan whole directories using FTP and if that also
    fails it scans the hosts file by file using HTTP.
    Canary mode only tries to determine if the mirror is up and
    repodata mode only scans all the repodata/ directories."""
    global timeout
    rc = 0
    successful_categories = 0
    host = mirrormanager2.lib.get_host(session, host)
    host_category_dirs = {}
    if host.private and not options["include_private"]:
        return 1
    http_debuglevel = 0
    ftp_debuglevel = 0
    if options["debug"]:
        http_debuglevel = 2
        ftp_debuglevel = 2

    hoststate = hostState(
        http_debuglevel=http_debuglevel,
        ftp_debuglevel=ftp_debuglevel,
        # This used to be the same timout as for the whole category.
        # This does not make much sense as according to the documentation
        # ...If the optional timeout parameter is given, blocking operations
        # ...(like connection attempts) will timeout after that many seconds
        # ...(if it is not given, the global default timeout setting is used)...
        # Setting this to '1' should limit the connection establishment to
        # to 1 minute.
        timeout_minutes=1,
    )

    categoryUrl = ""
    host_categories_to_scan = select_host_categories_to_scan(session, options, host)

    if not host_categories_to_scan:
        # If the host has no categories do not auto-disable it.
        # Just skip the host. rc == 12 do not reset auto-disable
        return 12

    for hc in host_categories_to_scan:
        timeout_check()
        if hc.always_up2date and not options["propagation"]:
            successful_categories += 1
            continue
        category = hc.category

        host_category_urls = [hcurl.url for hcurl in hc.urls]

        if options["propagation"]:
            return check_propagation(
                session,
                category.name,
                category.topdir.name,
                host_category_urls,
                options["proppath"],
            )

        categoryUrl = method_pref(host_category_urls)
        if categoryUrl is None:
            continue
        categoryPrefixLen = len(category.topdir.name)
        if categoryPrefixLen > 0:
            categoryPrefixLen += 1

        if options["continents"]:
            # Only check for continent if something specified
            # on the command-line
            rc = check_continent(categoryUrl)
            if rc == 8:
                raise WrongContinent
            if rc != 0:
                return rc

        if options["canary"]:
            logger.info("canary scanning category %s" % category.name)
        elif options["repodata"]:
            logger.info("repodata scanning category %s" % category.name)
        else:
            logger.info("scanning category %s" % category.name)

        # Check if either the http or ftp URL of the host point
        # to an existing and readable URL
        exists = check_for_base_dir(hoststate, host_category_urls)

        if not exists:
            # Base categoryURL for the current host was not found.
            # Skipping this category.
            continue

        # Record that this host has at least one (or more) categories
        # which is accessible via http or ftp
        successful_categories += 1

        if options["canary"]:
            continue

        trydirs = list(hc.category.directories)

        # No rsync in canary mode, we only retrive a small subset of
        # existing files
        if not options["repodata"]:
            # check the complete category in one go with rsync
            try:
                has_all_files = try_per_category(
                    session,
                    trydirs,
                    categoryUrl,
                    host_category_dirs,
                    hc,
                    host,
                    categoryPrefixLen,
                    config,
                )
            except TimeoutException:
                # If the crawl of only one category fails, the host
                # is completely marked as not being up to date.
                raise

            if has_all_files:
                # all files in this category are up to date, or not
                # no further checks necessary
                # do the next category
                continue

        # has_all_files is None, we don't know what failed, but something did
        # change preferred protocol if necessary to http or ftp
        categoryUrl = method_pref(host_category_urls, categoryUrl)

        try_later_delay = 1
        for d in trydirs:
            timeout_check()

            if not d.readable:
                continue

            if options["repodata"]:
                if not d.name.endswith("/repodata"):
                    continue

            dirname = d.name[categoryPrefixLen:]
            url = f"{categoryUrl}/{dirname}"

            try:
                has_all_files = try_per_dir(d, hoststate, url)
                if has_all_files is None:
                    has_all_files = try_per_file(d, hoststate, url)
                if has_all_files is False:
                    logger.warning("Not up2date: %s" % (d.name))
                    host_category_dirs[(hc, d)] = False
                elif has_all_files is True:
                    host_category_dirs[(hc, d)] = True
                    logger.info(url)
                    # make sure our parent dirs appear on the list too
                    host_category_dirs = add_parents(session, host_category_dirs, hc, d)
                else:
                    # could be a dir with no files, or an unreadable dir.
                    # defer decision on this dir, let a child decide.
                    pass

                # We succeeded, let's reduce the try_later_delay
                if try_later_delay > 1:
                    try_later_delay = try_later_delay >> 1
            except TryLater:
                msg = f"Server load exceeded on {host!r} - try later ({try_later_delay} seconds)"
                logger.warning(msg)
                if categoryUrl.startswith("http") and not hoststate.keepalives_available:
                    logger.warning(
                        "Host %s (id=%d) does not have HTTP Keep-Alives "
                        "enabled." % (host.name, host.id)
                    )

                time.sleep(try_later_delay)
                if try_later_delay < 60:
                    try_later_delay = try_later_delay << 1
            except TimeoutException:
                # If the crawl of only one category fails, the host
                # is completely marked as not being up to date.
                raise
            except Exception:
                logger.exception("Unhandled exception raised.")
                mark_not_up2date(
                    session,
                    config,
                    sys.exc_info(),
                    host,
                    "Unhandled exception raised.  " "This is a bug in the MM crawler.",
                )
                rc = 1
                break
        if categoryUrl.startswith("http") and not hoststate.keepalives_available:
            logger.warning(
                "Host %s (id=%d) does not have HTTP Keep-Alives enabled." % (host.name, host.id)
            )
    hoststate.close()

    if successful_categories == 0:
        if options["canary"]:
            # If running in canary mode do not auto disable mirrors
            # if they have failed. Therefore do not return '5' but
            # let's say '6'
            rc = 6
        else:
            # Let's say that '5' is the signal for the calling function
            # that all categories have failed due to broken base URLs
            # and that this host should me marked as failed during crawl
            rc = 5

    if rc == 0:
        if len(host_category_dirs) > 0:
            sync_hcds(session, host, host_category_dirs, options)
    del host_category_dirs
    return rc


def count_crawl_failures(host, config):
    try:
        host.crawl_failures += 1
    except TypeError:
        host.crawl_failures = 1

    auto_disable = config.get("CRAWLER_AUTO_DISABLE", 4)
    if host.crawl_failures >= auto_disable:
        host.disable_reason = (
            "Host has been disabled (user_active) after %d"
            " consecutive crawl failures" % auto_disable
        )
        host.user_active = False


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
        threadlocal.thread_id = thread_id()
        f = InjectingFilter(thread_id())
        fh.addFilter(f)

        if debug:
            fh.setLevel(logging.DEBUG)
        else:
            fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return log_file, fh


def worker(options, config, host_id):
    global current_host
    global threads_active
    global hosts_failed
    global timeout

    current_host = current_host + 1
    if timeout < 0:
        # And another new return value: 7 -> SIGARLM
        return 7

    db_manager = get_db_manager(config)
    session = db_manager.Session()
    host = mirrormanager2.lib.get_host(session, host_id)

    threads_active = threads_active + 1
    threadlocal.starttime = time.time()
    threadlocal.hostid = host.id
    threadlocal.hostname = host.name

    log_file = None
    fh = None
    if not options["propagation"]:
        log_file, fh = thread_file_logger(config.get("MM_LOG_DIR", None), host.id, options["debug"])

    logger.info(f"Worker {thread_id()!r} starting on host {host!r}")

    try:
        rc = per_host(session, host.id, options, config)

        # If 9 is returned the crawler is running in propagation test mode.
        if rc == 9:
            # Do not save any status about this run.
            threads_active = threads_active - 1
            session.close()
            return 0

        last_crawled = datetime.datetime.utcnow()
        last_crawl_duration = time.time() - threadlocal.starttime
        if rc == 5:
            # rc == 5 has been defined as a problem with all categories
            count_crawl_failures(host, config)
            hosts_failed += 1
        elif rc == 6:
            # rc == 6: canary mode has failed for all categories.
            # Let's mark the complete mirror as not being up to date.
            mark_not_up2date(
                session,
                config,
                None,
                host,
                "Canary mode failed for all categories. " "Marking host as not up to date.",
            )
            hosts_failed += 1
        elif rc == 12:
            # rc == 12: no category to crawl found. This is to make sure,
            # that host.crawl_failures is not reset to zero for crawling
            # non existing categories on this host
            logger.info("No categories to crawl on host %r" % host)
        else:
            # Resetting as this only counts consecutive crawl failures
            host.crawl_failures = 0
        host.last_crawled = last_crawled

        # Do not update last crawl duration in canary/repodata mode.
        # This duration is completely different from the real time
        # required to crawl the complete host so that it does not help
        # to remember it.
        if not (options["repodata"] or options["canary"]):
            if rc != 12:
                # rc == 12: no category to crawl found. No need to
                # update the crawl duration.
                host.last_crawl_duration = last_crawl_duration

        session.commit()
    except TimeoutException:
        rc = 2
        mark_not_up2date(
            session,
            config,
            None,
            host,
            "Crawler timed out before completing.  " "Host is likely overloaded.",
        )
        host.last_crawled = datetime.datetime.utcnow()
        host.last_crawl_duration = time.time() - threadlocal.starttime
        count_crawl_failures(host, config)
        hosts_failed += 1
        session.commit()
    except WrongContinent:
        logger.info("Skipping %r; wrong continent" % host)
        rc = 8
        # Delete log file for wrong continent mirrors as it contains
        # no useful information.
        if log_file:
            os.unlink(log_file)
    except Exception:
        logger.exception(f"Failure in thread {thread_id()!r}, host {host!r}")
        rc = 3

    logger.info(f"Ending crawl of {host!r} with status {rc!r}")
    if fh:
        logger.removeHandler(fh)
        fh.close()
    session.close()
    threads_active = threads_active - 1
    gc.collect()
    return rc


if __name__ == "__main__":
    sys.exit(main())
