# Copyright (C) 2008 by Alexander Koenig
# Copyright (C) 2008, 2015 by Adrian Reber
# Copyright (C) 2024 by Aurélien Bompard
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

import gzip
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta

import click

from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import AccessStat, AccessStatCategory

from .common import read_config

logger = logging.getLogger("mirrorlist-statistics")


def setup_logging(debug=False):
    format = "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"
    datefmt = "%m/%d/%Y %I:%M:%S %p"
    logging.basicConfig(format=format, datefmt=datefmt)

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


@click.command()
@click.option(
    "-c",
    "--config",
    envvar="MM2_CONFIG",
    default="/etc/mirrormanager/mirrormanager2.cfg",
    help="Configuration file to use",
)
@click.option(
    "-l",
    "--log",
    "logfile",
    type=click.Path(),
    help="gzipped logfile which should be used as input",
)
@click.option(
    "-o",
    "--offset",
    type=int,
    default=0,
    help=(
        "number of days which should be subtracted from today's date and be used as basis "
        "for log analysis",
    ),
)
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
def main(config, logfile, offset, debug):
    config = read_config(config)
    setup_logging(debug)
    db_manager = get_db_manager(config)
    session = db_manager.Session()
    logger.info("Starting mirrorlist statistics generator")

    start = time.monotonic()

    date = datetime.today() - timedelta(days=offset)

    stats = parse_logfile(date, config, logfile)

    stats_store = StatsStore(session, date, stats["accesses"])
    stats_store.store("countries", stats["countries"])
    stats_store.store("archs", stats["archs"])
    stats_store.store("repositories", stats["repositories"])

    session.commit()
    logger.info(f"Mirrorlist statistics gathered in {time.monotonic() - start}s")


def parse_logfile(date, config, logfile):
    accesses = 0
    countries = defaultdict(lambda: 0)
    repositories = defaultdict(lambda: 0)
    archs = defaultdict(lambda: 0)
    for line in gzip.open(logfile):
        arguments = line.split()
        try:
            y, m, d = arguments[3][:10].split("-")
        except Exception:
            continue
        if not ((int(y) == date.year) and (int(m) == date.month) and (int(d) == date.day)):
            continue
        country_code = arguments[5][:2]
        if country_code in config["EMBARGOED_COUNTRIES"]:
            countries["N/"] += 1
        else:
            countries[country_code] += 1
        archs[arguments[9]] += 1
        repositories[arguments[7][: len(arguments[7]) - 1]] += 1
        accesses += 1
    return {
        "countries": countries,
        "repositories": repositories,
        "archs": archs,
        "accesses": accesses,
    }


class StatsStore:
    def __init__(self, session, date, accesses):
        self.session = session
        self.date = date
        self.accesses = accesses

    def store(self, category_name, stats):
        category, _create = AccessStatCategory.get_or_create(name=category_name)
        for name, requests in stats.items():
            stat = AccessStat(
                category_id=category.id,
                date=self.date,
                name=name,
                requests=requests,
                percent=(float(requests) / float(self.accesses)) * 100,
            )
            self.session.add(stat)
        self.session.flush()
