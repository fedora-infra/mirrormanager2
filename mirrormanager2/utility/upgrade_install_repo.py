"""
This script changes the directory path from the fedora-install-X repositories
for a given version.

This can be used several time during the release cycle to move a repo from
a beta state to a release state.

This is currently kind of a work-around until the logic can be added into
the UMDL script.

TODO: test IRL
"""

import os
import warnings

import click

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager

from .common import config_option

# moving from pub/fedora/linux/releases/test/22_Beta/Server/x86_64/os/
# to          pub/fedora/linux/releases/22/Server/x86_64/os
# TODO: adjust the UMDL to do this


def move_install_repo(session, version, test=False, debug=False):
    """Move the install repo for the specified version to their release
    path.
    """
    product = mirrormanager2.lib.get_product_by_name(session, "Fedora")
    ver = mirrormanager2.lib.get_version_by_name_version(session, product.name, version)

    if not ver:
        print(f"No version found for {product.name}-{version}")
        return

    for a in mirrormanager2.lib.get_arches(session):
        if a.name == "source":
            continue

        if version == "development":
            # We do not change development repos
            continue

        prefix = "fedora-install-%s" % ver.name
        if a.primary_arch:
            d = f"pub/fedora/linux/releases/{ver.name}/Server/{a.name}/os"
            category = mirrormanager2.lib.get_category_by_name(session, "Fedora Linux")
        else:
            d = f"pub/fedora-secondary/releases/{ver.name}/Server/{a.name}/os"
            category = mirrormanager2.lib.get_category_by_name(session, "Fedora Secondary Arches")

        if not test:
            if not os.path.isdir(os.path.join("/srv", d)):
                print(
                    "directory %s does not exist on disk, skipping "
                    "creation of a repository there" % d
                )
                continue

        dobj = mirrormanager2.lib.get_directory_by_name(session, d)

        if not dobj:
            print(
                "directory %s exists on disk, but not in the database"
                " yet, skipping creation of a repository there until "
                "after the next UMDL run." % d
            )
            continue

        repo = mirrormanager2.lib.get_repo_prefix_arch(session, prefix, a.name)
        if not repo:
            print(f"No repo found for prefix: {prefix} - arch: {a.name}")
            continue

        print("Updating %s" % repo)
        print(f"Updating {repo.prefix} repo for arch {a.name}")

        if debug:
            print(f"{repo.version_id}   becomes   {ver.id}")
            print(f"{repo.arch_id}   becomes   {a.id}")
            print(f"{repo.name}   becomes   {dobj.name}")
            print(f"{repo.directory_id}   becomes   {dobj.id}")
            print(f"{repo.category_id}   becomes   {category.id}")
        else:
            repo.version_id = ver.id
            repo.arch_id = a.id
            repo.name = dobj.name
            repo.directory_id = dobj.id
            repo.category_id = category.id
            session.add(repo)
            session.flush()

    session.commit()


@click.command()
@config_option
@click.option(
    "--version",
    help="OS version to move (e.g. '14') [required]",
    required=True,
)
@click.option(
    "--test",
    is_flag=True,
    default=False,
    help="Small flag used for the unit-tests to avoid one check",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Output what changes but do not change anything",
)
def main(config, version, test, debug):
    warnings.warn(
        "This command is deprecated and will be removed in the next version. "
        "Please open a ticket at https://github.com/fedora-infra/mirrormanager2/issues "
        "if you still need it.",
        DeprecationWarning,
        stacklevel=1,
    )
    conf = mirrormanager2.lib.read_config(config)
    db_manager = get_db_manager(conf)
    session = db_manager.Session()

    move_install_repo(session, version, test=test, debug=debug)
