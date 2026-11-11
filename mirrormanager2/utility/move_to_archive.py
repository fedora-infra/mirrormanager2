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


def archive_directory_name(repo, archive_cat, live_cat):
    archivetopdir = archive_cat.topdir.name
    if live_cat is None:
        subdir = repo.directory.name
        if subdir.startswith(SKIP_DIR_PREFIX):
            subdir = subdir[len(SKIP_DIR_PREFIX) :]
        return os.path.join(archivetopdir, subdir)
    livetopdir = live_cat.topdir.name.rstrip("/") + "/"
    if not repo.directory.name.startswith(livetopdir):
        raise click.ClickException(
            f"{repo.directory.name} is not below {live_cat.topdir.name}, "
            f"the top directory of [{live_cat.name}]"
        )
    return os.path.join(archivetopdir, repo.directory.name[len(livetopdir) :])


def move_repos(session, archive_cat, dry_run, live_cat=None, **repo_query_args):
    repos = mirrormanager2.lib.get_repositories(session, **repo_query_args)
    moves = []
    for repo in repos:
        if live_cat is not None and repo.category != live_cat:
            continue
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

        target_dir = archive_directory_name(repo, archive_cat, live_cat)
        new_d = mirrormanager2.lib.get_directory_by_name(session, target_dir)
        if new_d is None:
            raise click.ClickException(
                f"Unable to find a directory in [{archive_cat.name}] for {repo.directory.name}"
            )
        moves.append((repo, new_d))

    # All archive directories are looked up before the first repository changes, so a
    # missing directory leaves every selected repository in its live category.
    for repo, new_d in moves:
        click.echo(f"{repo.directory.name} => {new_d.name}")
        if not dry_run:
            repo.directory = new_d
            repo.category = archive_cat
    if not dry_run:
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
    "--category",
    metavar="CATEGORY",
    help=(
        "Only move the repositories of this category. Their archive directory is "
        "their directory with the top directory of CATEGORY replaced by the top "
        "directory of the archive category. Without this option, the archive "
        "directory is the top directory of the archive category followed by the "
        "repository directory without its leading 'pub/'."
    ),
)
@click.option(
    "--dry-run",
    help="Only show what would be done, don't commit to the database",
    is_flag=True,
    default=False,
)
def main(config, product, version, repository, archive_category, category, dry_run):
    d = mirrormanager2.lib.read_config(config)
    db_manager = get_db_manager(d)
    session = db_manager.Session()

    archive_cat = mirrormanager2.lib.get_category_by_name(session, archive_category)
    if archive_cat is None:
        raise click.BadOptionUsage(
            "--archive-category", f"No category could be found by the name: {archive_category}"
        )

    live_cat = None
    if category:
        live_cat = mirrormanager2.lib.get_category_by_name(session, category)
        if live_cat is None:
            raise click.BadOptionUsage(
                "--category", f"No category could be found by the name: {category}"
            )

    if repository:
        move_repos(session, archive_cat, dry_run, live_cat, prefix=repository)
    elif product and version:
        if mirrormanager2.lib.get_product_by_name(session, product) is None:
            raise click.BadOptionUsage("--product", f"No such product: {product}")
        if mirrormanager2.lib.get_version_by_name_version(session, product, version) is None:
            raise click.BadOptionUsage("--version", f"No such version: {version}")
        move_repos(
            session, archive_cat, dry_run, live_cat, product_name=product, version_name=version
        )
    else:
        raise click.UsageError("You need to pass either the repository or both product and version")
