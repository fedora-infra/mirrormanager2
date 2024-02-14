import datetime
import logging
import sys
from dataclasses import dataclass
from enum import Enum

import mirrormanager2.lib
from mirrormanager2.lib.constants import PROPAGATION_ARCH
from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import HostCategoryDir, PropagationStatus

from .connection_pool import ConnectionPool
from .connector import FetchingFailed, SchemeNotAvailable
from .constants import REPODATA_DIR, REPODATA_FILE
from .continents import BrokenBaseUrl, EmbargoedCountry, WrongContinent, check_continent
from .reporter import Reporter
from .threads import ThreadTimeout, get_thread_id, on_thread_started
from .ui import ProgressTask

logger = logging.getLogger("crawler")


class CrawlerError(Exception):
    pass


class AllCategoriesFailed(CrawlerError):
    pass


class NoCategory(CrawlerError):
    pass


class CategoryNotAccessible(CrawlerError):
    pass


class CrawlStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass
class CrawlResult:
    host_id: int
    host_name: str
    status: str
    duration: int
    total_directories: int | None = None
    unreadable: int | None = None
    up2date: int | None = None
    not_up2date: int | None = None
    unchanged: int | None = None
    unknown: int | None = None
    hcds_created: int | None = None
    hcds_deleted: int | None = None


@dataclass
class PropagationResult:
    host_id: int
    host_name: str
    repo_status: dict[int, PropagationStatus]


def get_preferred_urls(host_category):
    """return which of the hosts connection method should be used
    rsync > http(s) > ftp"""
    urls = [hcurl.url for hcurl in host_category.urls if hcurl.url is not None]

    def _preferred_method(url):
        if url.startswith("rsync:"):
            return 1
        elif url.startswith("ftp:"):
            return 2
        elif url.startswith("http:"):
            return 3
        elif url.startswith("https:"):
            return 4
        else:
            return 5

    urls.sort(key=_preferred_method)
    return urls


class Crawler:
    def __init__(self, config, session, options, progress, host):
        self.config = config
        self.options = options
        self.session = session
        self.progress = progress
        self.host = host
        self.connection_pool = ConnectionPool(
            config, debuglevel=2 if options["debug"] else 0, timeout=options["host_timeout"]
        )
        self.timeout = ThreadTimeout(options["host_timeout"])
        self.host_category_dirs = {}

    def _parent(self, directory):
        parentDir = None
        splitpath = directory.name.split("/")
        if len(splitpath[:-1]) > 0:
            parentPath = "/".join(splitpath[:-1])
            parentDir = mirrormanager2.lib.get_directory_by_name(self.session, parentPath)
        return parentDir

    def add_parents(self, host_category_dirs, hc, d):
        parentDir = self._parent(d)
        if parentDir is not None:
            if (hc, parentDir) not in host_category_dirs:
                host_category_dirs[(hc, parentDir)] = None
            if parentDir != hc.category.topdir:  # stop at top of the category
                return self.add_parents(host_category_dirs, hc, parentDir)

        return host_category_dirs

    def select_host_categories_to_scan(self, ignore_empty=False):
        result = []
        if self.options["categories"]:
            for category in self.options["categories"]:
                hc = mirrormanager2.lib.get_host_category_by_hostid_category(
                    self.session, host_id=self.host.id, category=category
                )
                if hc is not None:
                    result.append(hc)
        else:
            result = list(self.host.categories)
        if not result and not ignore_empty:
            # If the host has no categories do not auto-disable it. Just skip the host.
            raise NoCategory
        return result

    def crawl(self):
        """This function scans all categories a host has defined.
        If a RSYNC URL is available it tries to scan the host requiring
        only single network connection. If this is not possible or fails
        it tries to scan whole directories using FTP and if that also
        fails it scans the hosts file by file using HTTP.
        Canary mode only tries to determine if the mirror is up and
        repodata mode only scans all the repodata/ directories."""
        self.timeout.start()
        successful_categories = 0
        host_category_dirs = {}

        host_categories_to_scan = self.select_host_categories_to_scan()
        # self.progress.set_total(len(host_categories_to_scan))
        # print(self.host, len(host_categories_to_scan))

        for hc in host_categories_to_scan:
            self.timeout.check()
            # self.progress.advance()
            if hc.always_up2date:
                successful_categories += 1
                continue
            try:
                result = self._scan_host_category(hc)
            except CategoryNotAccessible:
                result = None
            else:
                # Record that this host has at least one (or more) categories
                # which is accessible via http or ftp
                successful_categories += 1
            host_category_dirs.update(result or {})

        self.connection_pool.close_all()

        if successful_categories == 0:
            raise AllCategoriesFailed

        return host_category_dirs

    def check_for_base_dir(self, urls):
        """Check if at least one of the given URL exists on the remote host.
        This is used to detect mirrors which have completely dropped our content.
        This is only looking at http and ftp URLs as those URLs are actually
        relevant for normal access. If both tests fail the mirror will be marked
        as failed during crawl.
        """
        client_urls = [url for url in urls if url.startswith("http:")]
        for url in client_urls:
            connector = self.connection_pool.get(url)
            try:
                exists = connector.check_url(url)
            except Exception as e:
                exists = False
                logger.info("Could not get the base dir on %s: %s", url, e)
            finally:
                # Must close, or it will be reused for all schemes
                connector.close()
            if not exists:
                logger.warning("Base URL %s does not exist.", url)
                continue
            # The base http URL seems to work. Good!
            return True
        # Reaching this point means that no functional http/ftp has been
        # found. This means that the mirror will not work for normal http
        # and ftp users.
        return False

    def _scan_host_category(self, hc):
        category = hc.category
        urls = get_preferred_urls(hc)
        if not urls:
            raise CategoryNotAccessible

        if self.options["continents"]:
            # Only check for continent if something specified
            # on the command-line
            check_continent(self.config, self.options, self.session, urls[0])

        if not self.check_for_base_dir(urls):
            raise CategoryNotAccessible
        if self.options["canary"]:
            return

        category_prefix_length = len(category.topdir.name)
        if category_prefix_length > 0:
            category_prefix_length += 1

        msg = f"scanning category {category.name}"
        if self.options["canary"]:
            msg = f"canary {msg}"
        elif self.options["repodata"]:
            msg = f"repodata {msg}"
        logger.debug(msg)

        trydirs = list(hc.category.directories)
        if self.options["repodata"]:
            trydirs = [d for d in trydirs if d.name.endswith("/repodata")]
        self.progress.set_total(len(trydirs))

        host_category_dirs = {}

        while urls:
            try:
                url = urls.pop(0)
            except IndexError:
                break
            if url.endswith("/"):
                url = url[:-1]

            logger.debug("Crawling with URL %s", url)

            # No rsync in repodata mode, we only retrive a small subset of
            # existing files
            if self.options["repodata"] and url.startswith("rsync:"):
                continue

            connector = self.connection_pool.get(url)
            dir_statuses = connector.check_category(
                url, trydirs, category_prefix_length, self.timeout
            )
            try:
                for directory, dir_status in dir_statuses:
                    self.progress.advance()
                    host_category_dirs[(hc, directory)] = dir_status
                    if dir_status:
                        # make sure our parent dirs appear on the list too
                        host_category_dirs = self.add_parents(host_category_dirs, hc, directory)
                    else:
                        # logger.warning("Not up2date: %s", directory.name)
                        logger.debug("Not up2date: %s", directory.name)
            except SchemeNotAvailable:
                logger.debug(f"Scheme {url} is not available")
                continue

            # we know about the status of all files in this category
            # no further checks necessary
            # do the next category
            return host_category_dirs
        raise CategoryNotAccessible

    def sync_hcds(self, host_category_dirs):
        stats = dict(
            total_directories=0,
            up2date=0,
            not_up2date=0,
            unchanged=0,
            unreadable=0,
            unknown=0,
            hcds_created=0,
            hcds_deleted=0,
        )
        current_hcds = set()
        keys = host_category_dirs.keys()
        keys = sorted(keys, key=lambda t: t[1].name)
        stats["total_directories"] = len(keys)
        for hc, d in keys:
            status = host_category_dirs[(hc, d)]
            if status is None:
                stats["unknown"] += 1
                continue

            topname = hc.category.topdir.name
            toplen = len(topname)
            if d.name.startswith("/"):
                toplen += 1
            path = d.name[toplen:]

            hcd = mirrormanager2.lib.get_hostcategorydir_by_hostcategoryid_and_path(
                self.session, host_category_id=hc.id, path=path
            )
            if len(hcd) > 0:
                hcd = hcd[0]
            else:
                # don't create HCDs for directories which aren't up2date on the
                # mirror chances are the mirror is excluding that directory
                if not status:
                    continue
                hcd = HostCategoryDir(host_category_id=hc.id, path=path, directory_id=d.id)
                stats["hcds_created"] += 1

            if hcd.directory is None:
                hcd.directory = d
            if hcd.up2date != status:
                hcd.up2date = status
                self.session.add(hcd)
                if status is False:
                    logger.info("Directory %s is not up-to-date on this host." % d.name)
                    stats["not_up2date"] += 1
                else:
                    # logger.info(d.name)
                    stats["up2date"] += 1
            else:
                stats["unchanged"] += 1

            current_hcds.add(hcd.id)

        # In repodata mode we only want to update the files actually scanned.
        # Do not mark files which have not been scanned as not being up to date.
        if not self.options["repodata"]:
            # now-historical HostCategoryDirs are not up2date
            # we wait for a cascading Directory delete to delete this
            host_categories_to_scan = self.select_host_categories_to_scan(ignore_empty=True)
            for hc in host_categories_to_scan:
                for hcd in list(hc.directories):
                    if hcd.directory is not None and not hcd.directory.readable:
                        stats["unreadable"] += 1
                        continue
                    if hcd.id not in current_hcds and hcd.up2date is not False:
                        hcd.up2date = False
                        self.session.add(hcd)
                        stats["hcds_deleted"] += 1
        self.session.commit()
        return stats

    def check_propagation(self):
        self.timeout.start()
        repo_status = {}

        repos = mirrormanager2.lib.get_repositories(
            self.session,
            product_names=self.options["products"],
            version_names=self.options["versions"],
            prefixes=self.options["repo_prefixes"],
            arches=[PROPAGATION_ARCH],
        )
        if not repos:
            logger.warning("No repo found")
            return {}
        for repo in repos:
            repo_dir = repo.directory
            if repo_dir is None:
                logger.warning(
                    "No directory for repo with prefix %s on %s", repo.prefix, PROPAGATION_ARCH
                )
                continue
            repodata_dir = mirrormanager2.lib.get_directory_by_name(
                self.session, f"{repo_dir.name}/{REPODATA_DIR}"
            )
            if repodata_dir is None:
                logger.warning("Could not find the repodata dir for repo %s", repo)
                continue
            hc = mirrormanager2.lib.get_host_category_by_hostid_category(
                self.session, host_id=self.host.id, category=repo.category.name
            )
            if hc is None:
                continue
            self.timeout.check()
            topdir = repo.category.topdir.name
            url = self._get_http_url(hc)
            if url is None:
                logger.warning(
                    "Could not find a HTTP(s) URL for %s and %s. URLs: %s",
                    self.host,
                    repo.category,
                    repr(list(hc.urls)),
                )
                continue
            fd = mirrormanager2.lib.get_file_detail(
                self.session, REPODATA_FILE, repodata_dir.id, reverse=True
            )
            if fd is None:
                logger.warning(
                    "Could not find the file details for repo with prefix %s on %s",
                    repo.prefix,
                    PROPAGATION_ARCH,
                )
                continue
            checksum = self._get_checksum_for_repo(url, topdir, repodata_dir)
            status = self._get_file_propagation_status(fd, checksum)
            repo_status[repo.id] = status
        return repo_status

    def _get_http_url(self, host_category):
        for hcu in host_category.urls:
            url = hcu.url
            if url.startswith(("http:", "https:")):
                if not url.endswith("/"):
                    url += "/"
                return url

    def _get_checksum_for_repo(self, url, topdir, repo_dir):
        # Print out information about the repomd.xml status
        path = repo_dir.name
        if repo_dir.name.startswith(topdir):
            path = repo_dir.name[len(topdir) + 1 :]
        # fds = mirrormanager2.lib.get_file_detail_history(self.session, "repomd.xml", repo_dir.id)
        # sha256sums = {fd.sha256: fd.timestamp for fd in fds}

        logger.debug("Base URL: %s. Path: %s", url, path)
        url = f"{url}{path}/{REPODATA_FILE}"
        connector = self.connection_pool.get(url)
        try:
            csum = connector.get_sha256(url)
        except FetchingFailed as e:
            logger.info("Could not check %s: %s", url, e.response or "Connection error")
            return None
        return csum

    def _get_file_propagation_status(self, file_detail, checksum):
        if checksum is None:
            return PropagationStatus.NO_INFO
        today = datetime.datetime.combine(
            datetime.date.today(),
            datetime.time(hour=0, minute=0, second=0),
            tzinfo=datetime.timezone.utc,
        )
        age_threshold = today - datetime.timedelta(days=5)
        previous_file_detail = mirrormanager2.lib.get_file_details_with_checksum(
            self.session, file_detail, checksum, age_threshold
        )
        if previous_file_detail is None:
            return PropagationStatus.OLDER
        previous_ts = datetime.datetime.fromtimestamp(
            previous_file_detail.timestamp, tz=datetime.timezone.utc
        )
        if today - previous_ts > datetime.timedelta(days=3):
            return PropagationStatus.OLDER
        elif today - previous_ts > datetime.timedelta(days=2):
            return PropagationStatus.TWO_DAY
        elif today - previous_ts > datetime.timedelta(days=1):
            return PropagationStatus.ONE_DAY
        else:
            return PropagationStatus.SAME_DAY


def crawl_and_report(options, crawler):
    # Do not update last crawl duration in canary/repodata mode.
    # This duration is completely different from the real time
    # required to crawl the complete host so that it does not help
    # to remember it.
    host = crawler.host
    reporter = Reporter(crawler.config, crawler.session, crawler.host)

    record_duration = not options["repodata"] and not options["canary"]

    reporter.record_crawl_start()
    stats = {}
    try:
        host_category_dirs = crawler.crawl()
    except AllCategoriesFailed:
        if options["canary"]:
            # If running in canary mode do not auto disable mirrors
            # if they have failed.
            # Let's mark the complete mirror as not being up to date.
            reporter.mark_not_up2date(
                reason="Canary mode failed for all categories. Marking host as not up to date.",
            )
        else:
            # all categories have failed due to broken base URLs
            # and that this host should me marked as failed during crawl
            reporter.record_crawl_failure()
        status = CrawlStatus.FAILURE
    except TimeoutError:
        reporter.mark_not_up2date(
            reason="Crawler timed out before completing.  Host is likely overloaded.",
        )
        reporter.record_crawl_failure()
        status = CrawlStatus.FAILURE
    except WrongContinent:
        logger.info("Skipping host %s (%s); wrong continent", host.id, host.name)
        status = CrawlStatus.UNKNOWN
    except BrokenBaseUrl:
        logger.info("Skipping host %s (%s); broken base URL", host.id, host.name)
        status = CrawlStatus.UNKNOWN
    except EmbargoedCountry as e:
        logger.info("Host %s (%s) is from an embargoed country: %s", host.id, host.name, e.country)
        reporter.disable_host(f"Embargoed country: {e.country}")
        status = CrawlStatus.FAILURE
    except NoCategory:
        # no category to crawl found. This is to make sure,
        # that host.crawl_failures is not reset to zero for crawling
        # non existing categories on this host
        logger.info("No categories to crawl on host %s (%s)", host.id, host.name)
        # No need to update the crawl duration.
        record_duration = False
        status = CrawlStatus.UNKNOWN
    except KeyboardInterrupt:
        record_duration = False
        status = CrawlStatus.UNKNOWN
    except Exception:
        logger.exception("Unhandled exception raised.")
        reporter.mark_not_up2date(
            reason="Unhandled exception raised. This is a bug in the MM crawler.",
            exc=sys.exc_info(),
        )
        status = CrawlStatus.FAILURE
    else:
        # Resetting as this only counts consecutive crawl failures
        reporter.reset_crawl_failures()
        stats = crawler.sync_hcds(host_category_dirs)
        status = CrawlStatus.SUCCESS

    reporter.record_crawl_end(record_duration=record_duration)

    result = CrawlResult(
        host_id=host.id,
        host_name=host.name,
        status=status.value,
        duration=crawler.timeout.elapsed(),
        **stats,
    )

    return result


def check_propagation_and_report(options, crawler):
    repo_status = crawler.check_propagation()
    return PropagationResult(
        host_id=crawler.host.id,
        host_name=crawler.host.name,
        repo_status=repo_status,
    )


def worker(options, config, progress_bar, host_id):
    progress = ProgressTask(progress_bar, host_id)
    db_manager = get_db_manager(config)
    with db_manager.Session() as session:
        host = mirrormanager2.lib.get_host(session, host_id)
        progress.set_host_name(host.name)

        on_thread_started(host_id=host_id, host_name=host.name)
        if host.private and not options["include_private"]:
            progress.finish()
            return

        logger.debug(f"Worker {get_thread_id()!r} starting on host {host.id} ({host.name})")

        crawler = Crawler(config, session, options, progress, host)

        if options.get("propagation", False):
            check_function = check_propagation_and_report
        else:
            check_function = crawl_and_report

        try:
            result = check_function(options, crawler)
        except Exception:
            logger.exception(f"Failure in thread {get_thread_id()!r}, host {host.id} ({host.name})")
            raise
        finally:
            progress.finish()
        session.commit()
        logger.debug(f"Ending crawl of host {host.id} ({host.name})")
    return result
