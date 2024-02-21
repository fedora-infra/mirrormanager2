import logging
import smtplib
import time
from datetime import datetime, timezone

from .threads import threadlocal

logger = logging.getLogger(__name__)


class Reporter:
    def __init__(self, config, session, host):
        self.config = config
        self.session = session
        self.host = host
        self.host_failed = False

    def send_email(self, report_str, exc):
        if not self.config.get("CRAWLER_SEND_EMAIL", False):
            return

        SMTP_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
        msg = """From: {}
    To: {}
    Subject: {} MirrorManager crawler report
    Date: {}

    """.format(
            self.config.get("EMAIL_FROM"),
            self.config.get("ADMIN_EMAIL"),
            self.host.name,
            time.strftime(SMTP_DATE_FORMAT),
        )

        msg += report_str + "\n"
        msg += "Log can be found at {}/{}.log\n".format(
            self.config.get("crawler.logdir"), str(self.host.id)
        )
        if exc is not None:
            msg += f"Exception info: type {exc[0]}; value {exc[1]}\n"
            msg += str(exc[2])
        try:
            smtp = smtplib.SMTP(self.config.get("SMTP_SERVER"))

            username = self.config.get("SMTP_USERNAME")
            password = self.config.get("SMTP_PASSWORD")

            if username and password:
                smtp.login(username, password)

            smtp.sendmail(self.config.get("SMTP_SERVER"), self.config.get("ADMIN_EMAIL"), msg)
        except Exception:
            logger.exception("Error sending email")
            logger.debug("Email message follows:")
            logger.debug(msg)

        try:
            smtp.quit()
        except Exception:
            pass

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
                "Host has been disabled (user_active) after %d"
                " consecutive crawl failures" % auto_disable
            )

    def disable_host(self, reason):
        self.host.disable_reason = reason
        self.host.user_active = False

    def record_crawl_start(self):
        threadlocal.starttime = time.monotonic()

    def record_crawl_end(self, record_duration=True):
        self.host.last_crawled = datetime.now(tz=timezone.utc)
        last_crawl_duration = time.monotonic() - threadlocal.starttime
        if record_duration:
            self.host.last_crawl_duration = last_crawl_duration

    def reset_crawl_failures(self):
        self.host.crawl_failures = 0
