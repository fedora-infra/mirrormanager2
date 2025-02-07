import logging
import smtplib
from datetime import datetime, timezone
from email.message import Message
from email.utils import format_datetime
from typing import TYPE_CHECKING

import mirrormanager2.lib as mmlib

from .notif import Notifier
from .states import CrawlStatus
from .utils import get_host_urls

if TYPE_CHECKING:
    from .crawler import CrawlResult


logger = logging.getLogger(__name__)


class Reporter:
    def __init__(self, config, session, host):
        self.config = config
        self.session = session
        self.host = host
        self.host_failed = False
        self._notifier = Notifier(config=self.config)

    def send_email(self, report_str, exc):
        if not self.config.get("CRAWLER_SEND_EMAIL", False):
            return

        msg = Message()
        msg["From"] = self.config.get("EMAIL_FROM")
        msg["To"] = self.config.get("ADMIN_EMAIL")
        msg["Subject"] = f"MirrorManager crawler report: {self.host.name}"
        msg["Date"] = format_datetime(datetime.now(tz=timezone.utc))

        host_urls = get_host_urls(self.host, config=self.config)
        content = [report_str, f"Log can be found at {host_urls['crawler_log']}"]
        if exc is not None:
            msg.append(f"Exception info: type {exc[0]}; value {exc[1]}")
            msg.append(str(exc[2]))
        msg.set_content("\n".join(content))

        logger.debug("Sending a email report about %s", self.host.name)
        try:
            smtp = smtplib.SMTP(self.config.get("SMTP_SERVER"))

            username = self.config.get("SMTP_USERNAME")
            password = self.config.get("SMTP_PASSWORD")

            if username and password:
                smtp.login(username, password)

            smtp.send_message(msg)
        except Exception:
            logger.exception("Error sending email")
            logger.debug("Email message follows:")
            logger.debug(msg)

        try:
            smtp.quit()
        except Exception:
            logger.exception("Error quitting the SMTP connection")

    def mark_not_up2date(self, reason="Unknown", exc=None):
        """This function marks a complete host as not being up to date.
        It usually is called if the scan of a single category has failed.
        This is something the crawler does at multiple places: Failure
        in the scan of a single category disables the complete host."""
        self.host_failed = True
        self.host.set_not_up2date(self.session)
        msg = f"Host {self.host.id} marked not up2date: {reason}"
        logger.warning(msg)
        self.session.commit()
        if exc is not None:
            logger.debug(f"{exc[0]} {exc[1]} {exc[2]}")
        self.send_email(msg, exc)

    def record_crawl_failure(self):
        self.host_failed = True
        try:
            self.host.crawl_failures += 1
        except TypeError:
            self.host.crawl_failures = 1

        auto_disable = self.config.get("CRAWLER_AUTO_DISABLE", 4)
        if self.host.crawl_failures >= auto_disable:
            self.disable_host(
                f"Host has been disabled (user_active) after {auto_disable}"
                " consecutive crawl failures"
            )

    def disable_host(self, reason):
        self.host.disable_reason = reason
        self.host.user_active = False
        self._notifier.notify_disabled(self.host)

    def enable_host(self):
        self.host.user_active = True
        self.host.disable_reason = None
        # Resetting as we only count consecutive crawl failures
        self.host.crawl_failures = 0

    # def record_crawl_end(self, record_duration=True):
    #     self.host.last_crawled = datetime.now(tz=timezone.utc)
    #     last_crawl_duration = time.monotonic() - threadlocal.starttime
    #     if record_duration:
    #         self.record_duration(last_crawl_duration)

    # def record_duration(self, duration):
    #     self.host.last_crawl_duration = duration


def store_crawl_result(config, options, session, crawl_result: "CrawlResult"):
    host = mmlib.get_host(session, crawl_result.host_id)
    host.last_crawled = crawl_result.finished_at
    reporter = Reporter(config, session, host)

    if crawl_result.status == CrawlStatus.FAILURE.value:
        if options["canary"]:
            # If running in canary mode do not auto disable mirrors
            # if they have failed.
            # Let's mark the complete mirror as not being up to date.
            reporter.mark_not_up2date(reason=crawl_result.details)
        else:
            # all categories have failed due to broken base URLs
            # and that this host should be marked as failed during crawl
            reporter.record_crawl_failure()

    elif crawl_result.status == CrawlStatus.TIMEOUT.value:
        reporter.mark_not_up2date(reason=crawl_result.details)
        reporter.record_crawl_failure()

    elif crawl_result.status == CrawlStatus.DISABLE.value:
        reporter.disable_host(crawl_result.details)

    elif crawl_result.status == CrawlStatus.OK.value:
        reporter.enable_host()

    if (
        crawl_result.status != CrawlStatus.UNKNOWN.value
        and not options["repodata"]
        and not options["canary"]
    ):
        # reporter.record_duration(crawl_result.duration)
        host.last_crawl_duration = crawl_result.duration

    session.commit()
