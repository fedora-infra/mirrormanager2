# Copyright (C) 2015 by Red Hat, Inc.
# Author: Patrick Uiterwijk <puiterwijk@redhat.com>
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
"""
This script is an emergency script meant for releng to be used if an very
important update has went out, and we want to make sure that clients pick up
the latest version of the repo, even if that means more load on the master
mirrors.
It does this by deleting all non-current file_detail entries for this specific
repository, resulting in no alternate file checksums in the pickle.
This will cause the metalink to not return any <alternates> entries, such that
only the very latest version of the repo is considered as up-to-date.
"""

import logging

import click

from mirrormanager2.lib import read_config
from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import Product, Repository, Version

from .common import config_option

logger = logging.getLogger(__name__)


def setup_logging():
    format = "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"
    logging.basicConfig(format=format)

    logger.setLevel(logging.INFO)


@click.command()
@config_option
@click.argument("product", help="Product to clear old filedetails for (Fedora, EPEL)")
@click.argument("version", help="VERSION to clear old filedetails for (20, 21)")
def main(config, product, version):
    config = read_config(config)

    db_manager = get_db_manager(config)
    session = db_manager.Session()

    setup_logging()

    product = session.query(Product).filter_by(name=product).first()
    if not product:
        message = f"No product {product} found"
        logger.error(message)
        raise click.BadArgumentUsage(message)

    version = session.query(Version).filter_by(name=version, product_id=product.id).first()
    if not version:
        message = f"No version {version} found"
        logger.error(message)
        raise click.BadArgumentUsage(message)

    repos = session.query(Repository).filter_by(version_id=version.id).all()
    if len(repos) < 1:
        message = f"No repos found for {product} version {version}"
        logger.error(message)
        raise click.BadArgumentUsage(message)

    for repo in repos:
        logger.info("Clearing for repo %s" % repo.name)
        deleted = repo.emergency_expire_old_file_details(session)

        if not deleted:
            logger.info("Unused repo")
        else:
            logger.info(
                "Older versions deleted: %s",
                ", ".join([filename for filename in deleted if deleted[filename] != 0]),
            )

    logger.info("Done.")
