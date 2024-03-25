"""
Delete Propagation Statistics that are older that the configured value.

This should be run automatically and regularly, ideally every day.
"""

import logging
from datetime import datetime, timedelta

import click

import mirrormanager2.lib as mmlib
from mirrormanager2.lib.database import get_db_manager

from .common import config_option, setup_logging

logger = logging.getLogger(__name__)


@click.command()
@config_option
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
def main(config, debug):
    config = mmlib.read_config(config)
    db_manager = get_db_manager(config)
    setup_logging(debug=debug)

    with db_manager.Session() as session:
        propagation_threshold = datetime.now() - timedelta(days=config["PROPAGATION_KEEP_DAYS"])
        mmlib.delete_expired_propagation(session, propagation_threshold)

        access_stat_threshold = datetime.now() - timedelta(days=config["ACCESS_STATS_KEEP_DAYS"])
        mmlib.delete_expired_access_stats(session, access_stat_threshold)

        ## This is actually done by Directory.age_file_details, but one day we may prefer doing it
        ## this way instead of building a filedetails cache etc.
        # file_details_threshold = datetime.now() - timedelta(days=config["MAX_STALE_DAYS"])
        # mmlib.delete_expired_file_details(session, file_details_threshold)

        session.commit()
