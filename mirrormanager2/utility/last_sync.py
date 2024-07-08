# Copyright (C) 2014 by Adrian Reber
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import time

import click
import requests

fedora = "org.fedoraproject.prod.bodhi.updates.fedora.sync"
epel = "org.fedoraproject.prod.bodhi.updates.epel.sync"

branched = "org.fedoraproject.prod.compose.branched.rsync.complete"
rawhide = "org.fedoraproject.prod.compose.rawhide.rsync.complete"

base_url = "https://apps.fedoraproject.org/datagrepper/raw"


topics = []


def getKey(item):
    return item[1]


def create_url(url, topics, delta):
    topic = ""
    for i in topics:
        topic += f"&topic={i}"
    return f"{url}?delta={delta}{topic}"


def append_to_topics(*distros):
    def option_cb(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return
        topics.extend(distros)

    return option_cb


@click.command()
@click.option(
    "-a",
    "--all",
    is_flag=True,
    help="query all possible releases (default)",
    expose_value=False,
    callback=append_to_topics(fedora, epel, branched, rawhide),
)
@click.option(
    "-f",
    "--fedora",
    is_flag=True,
    help="only query if fedora has been updated during <delta>",
    expose_value=False,
    callback=append_to_topics(fedora),
)
@click.option(
    "-e",
    "--epel",
    is_flag=True,
    help="only query if epel has been updated",
    expose_value=False,
    callback=append_to_topics(epel),
)
@click.option(
    "-r",
    "--rawhide",
    is_flag=True,
    help="only query if rawhide has been updated",
    expose_value=False,
    callback=append_to_topics(rawhide),
)
@click.option(
    "-b",
    "--branched",
    is_flag=True,
    help="only query if the branched off release has been updated",
    expose_value=False,
    callback=append_to_topics(branched),
)
@click.option(
    "-q", "--quiet", is_flag=True, default=False, help="do not print out any informations"
)
@click.option(
    "-d",
    "--delta",
    default=86400,
    help="specify the time interval which should be used for the query (default: 86400)",
)
def main(quiet, delta):
    """Queries the Fedora Message Bus if new data is available on the public servers.

    Return 0 and no output if a sync happened during <delta>.
    If no sync happened 1 is returned.
    """
    global topics
    if topics == []:
        topics = [fedora, epel, branched, rawhide]

    data = requests.get(create_url(base_url, topics, delta)).json()

    repos = []

    for i in range(0, data["count"]):
        try:
            repo = "{}-{}".format(
                data["raw_messages"][i]["msg"]["repo"],
                data["raw_messages"][i]["msg"]["release"],
            )
        except Exception:
            # the rawhide and branch sync message has no repo information
            arch = data["raw_messages"][i]["msg"]["arch"]
            if arch == "":
                arch = "primary"
            repo = "{}-{}".format(data["raw_messages"][i]["msg"]["branch"], arch)

        repos.append([repo, data["raw_messages"][i]["timestamp"]])

    if quiet is False:
        for repo, timestamp in sorted(repos, key=getKey):
            print(
                "{}: {}".format(
                    repo, time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(timestamp))
                )
            )

    if data["count"] == 0:
        raise click.Abort()
