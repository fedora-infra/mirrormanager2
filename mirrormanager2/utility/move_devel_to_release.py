"""
This script changes the directory path from the development tree to the
released tree once the release has been published.

In principle it should be run about a week after the said release has been
published.

This implies that for a week, users will be actually hitting the development
tree (which is hardlinked to the release tree and thus will have the same
content)
"""

import os
import re

import click

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager

from .common import read_config


def fixup_repos(session, version, repo, new_dir):
    """
    This function does the actual changes in the database.
    The version, directory ID and name are adapted to point
    to the release tree and not to the development tree.

    This functions has changed a lot since MM1. Now the given
    repository is updated to point to the right directory and the
    name is changed to reflect the new directory.

    :param session: SQLAlchemy session
    :param version: A MM version object
    :param repo: The repository object which will be changed
    :param new_dir: The directory object which will be used now
    """
    repo.name = new_dir.name
    repo.version = version
    repo.directory_id = new_dir.id
    session.add(repo)

    session.commit()


def move_devel_repo(session, category, version):
    """
    This function loops over all repositories of a :category: and checks
    if the directory name (d.name) includes the :version: string.

    If the directory name matches the :version: and includes
    'development' in the path name the fixup_repos() function is used
    to change the directory ID, version and name of the repository object.

    :param session: SQLAlchemy session
    :param category: the category name as a string
    :param version: the version to move from devel to release
    """

    c = mirrormanager2.lib.get_category_by_name(session, category)
    if c is None:
        message = f"Category {category!r} not found, exiting.\n"
        message += get_all_categories(session)
        raise click.ClickException(message)

    v = mirrormanager2.lib.get_version_by_name_version(session, c.product.name, version)
    if not v:
        raise click.ClickException(f"Version {version} not found for product {c.product.name}")

    oldpattern = os.path.join("development", version)
    newpattern = os.path.join("releases", version)
    oldRe = re.compile(oldpattern)
    for r in c.repositories:
        if not r.prefix:
            # This seems to be necessary for test cases using sqlite
            continue

        d = r.directory

        if not d:
            # Also not interested in repositories without
            # a directory.
            continue

        if oldRe.search(d.name):
            t = d.name.replace(oldpattern, newpattern)
            new_d = mirrormanager2.lib.get_directory_by_name(session, t)
            if new_d is None:
                click.echo(f"target Directory({t}) not found, ignoring.", err=True)
                continue

            if new_d.repositories:
                # The new directory already has a repository and will
                # thus lead to a duplicate key value violation.
                continue
            fixup_repos(session, v, r, new_d)
            print(f"{d.name} => {t}")


def get_all_categories(session):
    lines = ["Available categories:"]
    for c in mirrormanager2.lib.get_categories(session):
        lines.append(f"\t{c.name}")
    return "\n".join(lines)


@click.command()
@click.option(
    "-c",
    "--config",
    envvar="MM2_CONFIG",
    default="/etc/mirrormanager/mirrormanager2.cfg",
    help="Configuration file to use " "(default=/etc/mirrormanager/mirrormanager2.cfg)",
)
@click.option(
    "--version",
    help="OS version to move (e.g. '14') [required]",
    required=True,
)
@click.option(
    "--category",
    help="Category (e.g. 'Fedora Linux') [required]",
    default=None,
)
def main(config, version, category):
    d = read_config(config)
    db_manager = get_db_manager(d)
    session = db_manager.Session()

    if category is None:
        raise click.BadParameter(get_all_categories(session))

    move_devel_repo(session, category, version)
