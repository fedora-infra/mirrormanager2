"""
This script adds a product.
"""

import click
from sqlalchemy.exc import IntegrityError
from sqlalchemy_helpers import get_one

from mirrormanager2.lib import model, read_config
from mirrormanager2.lib.database import get_db_manager

from .common import config_option

DEFAULT_CATEGORY = "Fedora {name}"
DEFAULT_HOST = "dl.fedoraproject.org"
DIR_PREFIX = "pub/"


@click.command()
@config_option
@click.option(
    "-n",
    "--name",
    required=True,
    help="Product name",
)
@click.option(
    "-v",
    "--version",
    "versions",
    multiple=True,
    required=True,
    help="Versions currently available",
)
@click.option(
    "-c",
    "--category",
    help="Category",
)
@click.option(
    "--dry-run",
    help="Only show what would be done, don't commit to the database",
    is_flag=True,
    default=False,
)
def main(config, name, versions, category, dry_run):
    if not category:
        category = DEFAULT_CATEGORY.format(name=name)
    topdir = f"{DIR_PREFIX}{name.lower()}"

    d = read_config(config)
    db_manager = get_db_manager(d)
    session = db_manager.Session()

    product = model.Product(
        name=name,
        publiclist=True,
    )
    session.add(product)
    try:
        session.flush()
    except IntegrityError as e:
        raise click.ClickException(f"product {name!r} already exists.") from e
    click.echo(f"Added product {name!r}")

    topdir = model.Directory(
        name=topdir,
        files=b"",
        readable=True,
    )
    session.add(topdir)
    session.flush()
    click.echo(f"Added top directory {topdir.name!r}")

    category = model.Category(
        name=category,
        product_id=product.id,
        canonicalhost=f"https://{DEFAULT_HOST}",
        topdir_id=topdir.id,
        publiclist=True,
    )
    session.add(category)
    session.flush()
    click.echo(f"Added category {category.name!r}")

    cat_dir = model.CategoryDirectory(
        category_id=category.id,
        directory_id=topdir.id,
    )
    session.add(cat_dir)
    session.flush()
    click.echo("Added category directory")

    main_host = get_one(session, model.Host, name=DEFAULT_HOST)
    host_cat = model.HostCategory(
        category_id=category.id,
        host_id=main_host.id,
        always_up2date=True,
    )
    session.add(host_cat)
    session.flush()
    click.echo("Added host category")

    host_cat_url = model.HostCategoryUrl(
        host_category_id=host_cat.id,
        url=f"https://{DEFAULT_HOST}/{topdir}",
        private=False,
    )
    session.add(host_cat_url)
    session.flush()
    click.echo(f"Added host category URL {host_cat_url.url!r}")

    for version_name in versions:
        version = model.Version(
            name=version_name,
            product_id=product.id,
        )
        session.add(version)
        session.flush()
        click.echo(f"Added version {version.name!r}")

    if dry_run:
        session.rollback()
    else:
        session.commit()
