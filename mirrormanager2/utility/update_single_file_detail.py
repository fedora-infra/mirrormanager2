"""
This script is like the light-weight version of update-master-directory-list.
Instead of crawling *all* files on the nfs mount of the master mirror content,
and updating the mm2 database with what mirrors *should* have.. this script
looks at just a single master mirror file and updates its details in the
mm2 database.

This is not something that is run automatically or regularly, but should be
used by mm2 admins for surgery and quick regeneration of the pickle file.
"""

import hashlib
import logging
import os

import click
import rpmmd.repoMDObject

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import FileDetail

from .common import read_config

logger = logging.getLogger("mm2")


# Something like this is committed to yum upstream, but may not be in the
# copy we are using.
def set_repomd_timestamp(yumrepo):
    timestamp = 0
    for ft in yumrepo.fileTypes():
        thisdata = yumrepo.repoData[ft]
        timestamp = max(int(thisdata.timestamp), timestamp)
    yumrepo.timestamp = timestamp
    return timestamp


def setup_logging(debug=False):
    format = "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"
    datefmt = "%m/%d/%Y %I:%M:%S %p"
    logging.basicConfig(format=format, datefmt=datefmt)

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


@click.command()
@click.option(
    "-c",
    "--config",
    envvar="MM2_CONFIG",
    default="/etc/mirrormanager/mirrormanager2.cfg",
    help="Configuration file to use",
)
@click.option(
    "--category",
    "categories",
    metavar="CATEGORY",
    default=None,
    help="only scan category CATEGORY",
)
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
@click.option("--filename", type=click.Path(), default=None, help="path/to/file")
def main(config, categories, debug, filename):
    config = read_config(config)
    db_manager = get_db_manager(config)
    session = db_manager.Session()

    setup_logging(debug=debug)

    if not filename:
        logger.error("--filename is required")
        return 1

    check_categories = []
    if categories is None:
        check_categories = config.get("umdl_master_directories")
    else:
        for i in config.get("umdl_master_directories"):
            if i["category"] == categories:
                check_categories.append(i)

    for i in check_categories:
        cname = i["category"]
        logger.info("Considering category %s" % cname)

        category = mirrormanager2.lib.get_category_by_name(session, cname)
        if not category:
            logger.error("Category %s does not exist in the database, skipping" % (cname))
            continue

        if category.product is None:
            logger.error("umdl_master_directories Category %s has null Product, skipping" % (cname))
            logger.error("Category %s has null Product, skipping" % (cname))
            continue

        absolutepath = os.path.join(i["path"], filename)
        dirname = "/".join(absolutepath.strip("/").split("/")[1:-1])
        directory = mirrormanager2.lib.get_directory_by_name(session, dirname)

        if not directory:
            logger.error("Directory %s does not exist in the database, skipping" % (dirname))
            continue

        warning = "Won't make repo file details"

        if not os.path.exists(absolutepath):
            logger.error(f"{warning}: {absolutepath!r} does not exist")
            continue

        try:
            f = open(absolutepath, "rb")
            contents = f.read()
            f.close()
        except Exception:
            logger.exception("Error reading %r" % absolutepath)
            continue

        size = len(contents)
        md5 = hashlib.md5(contents).hexdigest()
        sha1 = hashlib.sha1(contents).hexdigest()
        sha256 = hashlib.sha256(contents).hexdigest()
        sha512 = hashlib.sha512(contents).hexdigest()

        target = filename.split("/")[-1]

        if target == "repomd.xml":
            yumrepo = rpmmd.repoMDObject.RepoMD("repoid", absolutepath)
            if "timestamp" not in yumrepo.__dict__:
                set_repomd_timestamp(yumrepo)
            timestamp = yumrepo.timestamp
        elif target == "summary":
            # TODO -- ostree repos may have a timestamp in their summary file
            # someday.  for now, just use the system mtime.
            timestamp = os.path.getmtime(absolutepath)

        fd = mirrormanager2.lib.get_file_detail(
            session,
            directory_id=directory.id,
            filename=target,
            sha1=sha1,
            md5=md5,
            sha256=sha256,
            sha512=sha512,
            size=size,
            timestamp=timestamp,
        )
        if not fd:
            fd = FileDetail(
                directory_id=directory.id,
                filename=target,
                sha1=sha1,
                md5=md5,
                sha256=sha256,
                sha512=sha512,
                timestamp=timestamp,
                size=size,
            )
            logger.info(f"Updating FileDetail {fd.filename}, {absolutepath!r}")
            session.add(fd)
            session.commit()
        else:
            logger.warning(f"FileDetail unchanged {absolutepath!r} ({fd.id})")

    logger.info("Done.")
