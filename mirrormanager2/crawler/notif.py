import logging

import mirrormanager2.lib

logger = logging.getLogger("crawler")


def notify(options, topic, msg):
    if not options["fedmsg"]:
        return

    mirrormanager2.lib.notifications.fedmsg_publish(
        f"mirrormanager.crawler.{topic}",
        msg,
    )


def _get_host_names(hosts, options):
    # Get a list of host names for fedmsg
    return [
        host.name
        for host in hosts
        if (not host.id < options["startid"] and not host.id >= options["stopid"])
    ]


def notify_start(hosts, options):
    host_names = _get_host_names(hosts, options)
    hostlist = [dict(id=id, host=host) for id, host in zip(hosts, host_names)]
    msg = dict(hosts=hostlist)
    msg["options"] = options
    notify(options, "start", msg)


def notify_complete(hosts, options, return_codes):
    # Put a bow on the results for fedmsg
    host_names = _get_host_names(hosts, options)
    results = [
        dict(rc=rc, host=host, id=id) for rc, host, id in zip(return_codes, host_names, hosts)
    ]
    notify(options, "complete", dict(results=results))
