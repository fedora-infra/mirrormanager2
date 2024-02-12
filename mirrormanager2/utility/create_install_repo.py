"""
This script creates the fedora-install repo for Fedora .
"""

import logging
import os
import warnings

import click

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import Repository

logger = None

# dict(subpath='Workstation/armhfp/os', prefix="fedora-workstation-%s", arch="armhfp"),
# dict(subpath='Workstation/i386/os', prefix="fedora-workstation-%s", arch="i386"),
# dict(subpath='Workstation/x86_64/os', prefix="fedora-workstation-%s", arch='x86_64'),
REPOS = [
    dict(subpath="Server/armhfp/os", prefix="fedora-install-%s", arch="armhfp"),
    dict(subpath="Server/i386/os", prefix="fedora-install-%s", arch="i386"),
    dict(subpath="Server/x86_64/os", prefix="fedora-install-%s", arch="x86_64"),
]
# dict(subpath='Server/aarch64/os', prefix="fedora-install-%s", arch="aarch64"),
# dict(subpath='Server/ppc64/os', prefix="fedora-install-%s", arch="ppc64"),
# dict(subpath='Server/ppc64le/os', prefix="fedora-install-%s", arch="ppc64le"),
# dict(subpath='Server/s390x/os', prefix="fedora-install-%s", arch="s390x"),


def add_one_repository(directory, category, version, prefix, arch):
    """Add a repository to the database based on the information provided."""

    repo = Repository(
        prefix=prefix,
        version=version,
        arch=arch,
        name=directory.name,
        category=category,
        directory=directory,
    )
    logger.info(
        "Created Repository(prefix={}, version={}, arch={}, category={}) "
        "-> Directory {}".format(prefix, version.name, arch.name, category.name, directory.name)
    )
    return repo


def doit(session, version_name, category_name, parent):
    """Actually add the repositories to the database."""

    category = mirrormanager2.lib.get_category_by_name(session, category_name)
    if not category:
        print("No such category found: %s" % category_name)
        return 1
    ver = mirrormanager2.lib.get_version_by_name_version(
        session, category.product.name, version_name
    )
    if not ver:
        print("No such version found: %s" % version_name)
        return 1

    for r in REPOS:
        prefix = r["prefix"] % version_name
        arch = mirrormanager2.lib.get_arch_by_name(session, r["arch"])
        version = mirrormanager2.lib.get_version_by_name_version(
            session, p_name=category.product.name, p_version=version_name
        )
        d = os.path.join(parent, r["subpath"])
        directory = mirrormanager2.lib.get_directory_by_name(session, d)
        repo = mirrormanager2.lib.get_repo_prefix_arch(session, prefix=prefix, arch=arch.name)

        if not repo:
            repo = add_one_repository(directory, category, version, prefix, arch)
            logger.info(f"Added pointer ({repo.prefix}, {repo.arch}) to {d}")

        else:
            old_directory = repo.directory
            # do the updates
            repo.name = d
            repo.directory = directory
            repo.version = ver
            repo.category = category
            repo.arch = arch
            old_dir = old_directory.name if old_directory else None
            logger.info(f"Moved ({repo.prefix}, {repo.arch.name}) from {old_dir} to {d}")

        session.add(repo)


def setup_logger(debug):
    global logger
    logging.basicConfig()
    logger = logging.getLogger()
    if debug:
        logger.setLevel(logging.DEBUG)


@click.command()
@click.option(
    "-c",
    "--config",
    envvar="MM2_CONFIG",
    default="/etc/mirrormanager/mirrormanager2.cfg",
    help="Configuration file to use",
)
@click.option("--version", default="21", help="Version")
@click.option("--category", default="Fedora Other")
@click.option("--debug", is_flag=True, default=False)
@click.argument("base_install_path")
def main(config, version, category, debug, base_install_path):
    warnings.warn(
        "This command is deprecated and will be removed in the next version. "
        "Please open a ticket at https://github.com/fedora-infra/mirrormanager2/issues "
        "if you still need it.",
        DeprecationWarning,
        stacklevel=1,
    )
    config = mirrormanager2.lib.read_config(config)
    db_manager = get_db_manager(config)
    session = db_manager.Session()
    setup_logger(debug)
    doit(session, version, category, base_install_path)
    session.commit()
