"""
This script changes the directory path for a release once it goes EOL.

In principle it should be run about a week after the said release went EOL.
"""

import os

import click

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager

from .common import config_option

DEFAULT_ARCHIVE_CATEGORY = "Fedora Archive"
IGNORE_CATEGORIES = ["Fedora Codecs"]
SKIP_DIR_PREFIX = "pub/"


def move_repos(session, archive_cat, dry_run, **repo_query_args):
    archivetopdir = archive_cat.topdir.name
    repos = mirrormanager2.lib.get_repositories(session, **repo_query_args)
    for repo in repos:
        if repo.directory is None:
            click.echo(f"Repo {repo.name} (prefix {repo.prefix}) has no directory, skipping.")
            continue
        if repo.category == archive_cat:
            click.echo(f"Repo {repo.name} (prefix {repo.prefix}) is already archived, skipping.")
            continue
        if repo.category.name in IGNORE_CATEGORIES:
            click.echo(
                f"Repo {repo.name} (prefix {repo.prefix}) is in the "
                f"{repo.category.name!r} category, skipping."
            )
            continue

        subdir = repo.directory.name
        if subdir.startswith(SKIP_DIR_PREFIX):
            subdir = subdir[len(SKIP_DIR_PREFIX) :]
        target_dir = os.path.join(archivetopdir, subdir)
        new_d = mirrormanager2.lib.get_directory_by_name(session, target_dir)
        if new_d is None:
            raise click.ClickException(
                f"Unable to find a directory in [{archive_cat.name}] for {repo.directory.name}"
            )
        click.echo(f"{repo.directory.name} => {target_dir}")
        repo.directory = new_d
        repo.category = archive_cat
        if not dry_run:
            session.add(repo)
            session.commit()


@click.command()
@config_option
@click.option(
    "--product",
    help="Product name",
)
@click.option(
    "--version",
    help="Version to archive",
)
@click.option(
    "--repository",
    help="Repository to archive",
)
@click.option(
    "--archive-category",
    metavar="CATEGORY",
    help="Archive Category",
    default=DEFAULT_ARCHIVE_CATEGORY,
    show_default=1,
)
@click.option(
    "--dry-run",
    help="Only show what would be done, don't commit to the database",
    is_flag=True,
    default=False,
)
def main(config, product, version, repository, archive_category, dry_run):
    d = mirrormanager2.lib.read_config(config)
    db_manager = get_db_manager(d)
    session = db_manager.Session()

    archive_cat = mirrormanager2.lib.get_category_by_name(session, archive_category)
    if archive_cat is None:
        raise click.BadOptionUsage(
            "--archive-category", f"No category could be found by the name: {archive_category}"
        )

    if repository:
        move_repos(session, archive_cat, dry_run, prefix=repository)
    elif product and version:
        if mirrormanager2.lib.get_product_by_name(session, product) is None:
            raise click.BadOptionUsage("--product", f"No such product: {product}")
        if mirrormanager2.lib.get_version_by_name_version(session, product, version) is None:
            raise click.BadOptionUsage("--version", f"No such version: {version}")
        move_repos(session, archive_cat, dry_run, product_name=product, version_name=version)
    else:
        raise click.UsageError("You need to pass either the repository or both product and version")
