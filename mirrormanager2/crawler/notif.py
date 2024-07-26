import dataclasses
import logging

from fedora_messaging.api import Message

from mirrormanager2.lib.model import Host
from mirrormanager2.lib.notifications import fedmsg_publish

from .crawler import CrawlResult, PropagationResult

logger = logging.getLogger(__name__)


def notify(options, topic, msg):
    if not options["fedmsg"]:
        return

    message = Message(topic=f"mirrormanager.crawler.{topic}", body=msg)
    fedmsg_publish(message)


def notify_start(hosts: list[Host], options):
    hostlist = [dict(id=host.id, name=host.name) for host in hosts]
    msg = dict(hosts=hostlist)
    msg["options"] = options
    notify(options, "start", msg)


def notify_crawl_complete(options, results: list[CrawlResult]):
    results = [dataclasses.asdict(result) for result in results]
    notify(options, "crawl.complete", dict(results=results))


def notify_propagation_crawl_complete(options, results: list[PropagationResult]):
    results = [dataclasses.asdict(result) for result in results]
    notify(options, "propagation.complete", dict(results=results))
