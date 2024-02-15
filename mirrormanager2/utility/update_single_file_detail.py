"""
This script is like the light-weight version of update-master-directory-list.
Instead of crawling *all* files on the nfs mount of the master mirror content,
and updating the mm2 database with what mirrors *should* have.. this script
looks at just a single master mirror file and updates its details in the
mm2 database.

This is not something that is run automatically or regularly, but should be
used by mm2 admins for surgery and quick regeneration of the pickle file.
"""

import logging
import os

import click

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager

from .common import config_option, filter_master_directories, setup_logging

logger = logging.getLogger("mm2")


@click.command()
@config_option
@click.option(
    "--category",
    "categories",
    default=[],
    multiple=True,
    help="Category to scan (default=all), can be repeated, exclude by prefixing with '^'",
)
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
@click.argument("filename", type=click.Path(), required=True, help="path/to/file")
def main(config, categories, debug, filename):
    config = mirrormanager2.lib.read_config(config)
    db_manager = get_db_manager(config)

    setup_logging(debug=debug)

    with db_manager.Session() as session:
        master_dirs = filter_master_directories(config, session, categories)
        for master_dir in master_dirs:
            cname = master_dir["category"]
            logger.info("Considering category %s" % cname)
            # category = mirrormanager2.lib.get_category_by_name(session, cname)

            absolutepath = os.path.join(master_dir["path"], filename)
            # dirname = "/".join(absolutepath.strip("/").split("/")[1:-1])
            dirname = os.path.dirname(filename)
            # target = filename.split("/")[-1]
            target = os.path.basename(filename)

            directory = mirrormanager2.lib.get_directory_by_name(session, dirname)
            if not directory:
                logger.error("Directory %s does not exist in the database, skipping", dirname)
                continue

            repomaker = mirrormanager2.lib.umdl.RepoMaker(session, config)
            created = repomaker.make_file_details(directory, master_dir["path"], dirname, target)

            if created is False:
                logger.warning(f"FileDetail unchanged {absolutepath!r}")
            session.commit()

    logger.info("Done.")
