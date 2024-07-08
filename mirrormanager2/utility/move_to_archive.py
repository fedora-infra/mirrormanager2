"""
This script changes the directory path for a release once it goes EOL.

In principle it should be run about a week after the said release went EOL.
"""

import os
import re

import click

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager

from .common import config_option

archiveCategory = "Fedora Archive"
originalCategory = "Fedora Linux"


def doit(session, original_cat, archive_cat, directory_re):
    c = mirrormanager2.lib.get_category_by_name(session, original_cat)
    if c is None:
        raise click.ClickException(f"No category could be found by the name: {original_cat}")
    a = mirrormanager2.lib.get_category_by_name(session, archive_cat)
    if a is None:
        raise click.ClickException(f"No category could be found by the name: {archive_cat}")
    originaltopdir = c.topdir.name
    archivetopdir = os.path.join(a.topdir.name, "fedora", "linux")
    dirRe = re.compile(directory_re)
    for d in c.directories:
        if dirRe.search(d.name):
            for r in d.repositories:
                t = os.path.join(archivetopdir, d.name[len(originaltopdir) + 1 :])
                print(f"trying to find {t}")
                new_d = mirrormanager2.lib.get_directory_by_name(session, t)
                if new_d is None:
                    raise click.ClickException(
                        f"Unable to find a directory in [{archive_cat}] for {d.name}"
                    )
                r.directory = new_d
                r.category = a
                session.add(r)
                session.commit()
                print(f"{d.name} => {t}")


@click.command()
@config_option
@click.option(
    "--originalCategory",
    metavar="CATEGORY",
    help=f"original Category (default={originalCategory})",
    default=originalCategory,
)
@click.option(
    "--archiveCategory",
    metavar="CATEGORY",
    help=f"archive Category (default={archiveCategory})",
    default=archiveCategory,
)
@click.option(
    "--directoryRe",
    metavar="RE",
    required=True,
    help="subdirectory regular expression to move (e.g. '/7/') " "[required]",
)
def main(config, originalcategory, archivecategory, directoryre):
    d = mirrormanager2.lib.read_config(config)
    db_manager = get_db_manager(d)
    session = db_manager.Session()
    doit(session, originalcategory, archivecategory, directoryre)
