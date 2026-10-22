import logging

from mirrormanager_messages.host import HostCrawlerDisabledV1

from mirrormanager2.lib.model import Host
from mirrormanager2.lib.notifications import (
    fedmsg_publish,
    host_to_message_body,
    site_to_message_body,
)

from .utils import get_host_urls

logger = logging.getLogger(__name__)


class Notifier:

    def __init__(self, config: dict):
        self._config = config

    # def notify(self, topic, msg):
    #     message = Message(topic=f"mirrormanager.crawler.{topic}", body=msg)
    #     fedmsg_publish(message)

    # def notify_start(self, hosts: list[Host]):
    #     hostlist = [dict(id=host.id, name=host.name) for host in hosts]
    #     msg = dict(hosts=hostlist)
    #     self.notify("start", msg)

    # def notify_crawl_complete(self, results: list["CrawlResult"]):
    #     results = [dataclasses.asdict(result) for result in results]
    #     self.notify("crawl.complete", dict(results=results))

    # def notify_propagation_crawl_complete(self, results: list["PropagationResult"]):
    #     results = [dataclasses.asdict(result) for result in results]
    #     self.notify("propagation.complete", dict(results=results))

    def notify_disabled(self, host: Host):
        if not self._config.get("USE_FEDORA_MESSAGING", True):
            # Same switch the web UI honours; without a message bus every
            # publish attempt would wait for its timeout and then fail.
            logger.debug("Fedora Messaging is disabled, not notifying about %s", host.name)
            return
        host_urls = get_host_urls(host, config=self._config)
        body = {
            "site": site_to_message_body(host.site),
            "host": {
                **host_to_message_body(host),
                "url": host_urls["host"],
            },
            "crawled_at": host.last_crawled.isoformat(),
            "logs_url": host_urls["crawler_log"],
            "reason": host.disable_reason,
        }
        message = HostCrawlerDisabledV1(body=body)
        fedmsg_publish(message)
