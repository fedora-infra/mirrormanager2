"""
Delete Propagation Statistics that are older that the configured value.

This should be run automatically and regularly, ideally every day.
"""

import logging
from datetime import datetime, timedelta

import click

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager

from .common import config_option, setup_logging

logger = logging.getLogger("mm2")


@click.command()
@config_option
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
def main(config, debug):
    config = mirrormanager2.lib.read_config(config)
    db_manager = get_db_manager(config)
    setup_logging(debug=debug)

    threshold = datetime.now() - timedelta(days=config["PROPAGATION_KEEP_DAYS"])
    with db_manager.Session() as session:
        mirrormanager2.lib.delete_expired_propagation(session, threshold)
