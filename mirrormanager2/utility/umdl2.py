"""
This script crawls the local copy of the master mirrors (which in our case
is just a nfs mount of the master mirror content). According to what it
finds, it updates the mirrormanager2 database.
It will create new product/version if it finds them and drop directories if
they disappeared.

Basically, it checks the content of the nfs mount, if the directory
contains a lot of files, it takes the 3 most recents ones, stores them in
the DB and they will be used later on to check if the mirrors are up to date.
If the directory does not contain too many files, it will register them all
and thus will check them all on the mirrors.
The threshold is stored in: `short_filelist` and is currently at 10.

If the script finds a yum or atomic repository (finds a repo data or an atomic
summary file), it will create a repository object (cf `make_repository`) which
is basically a mapping between a yum repo name (ie: Fedora-20-updates) and a
directory (/pub/fedora/linux/updates/....)

"""

import logging
import logging.handlers
import os
import re
import stat
import warnings

import click

import mirrormanager2.lib
import mirrormanager2.lib.umdl as umdl
from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import Directory

from .common import read_config

logger = logging.getLogger("umdl")
stdexcludes = [r".*\.snapshot", r".*/\.~tmp~"]


def cache_directories(category):
    cache = dict()
    topdirName = category.topdir.name
    for directory in list(category.directories):
        relativeDName = umdl.remove_category_topdir(topdirName, directory.name).strip("/")
        cache[relativeDName] = directory
    return cache


def is_excluded(path, excludes):
    for e in excludes:
        if re.compile(e).match(path):
            return True
    return False


def sync_directories_from_fullfilelist(session, config, diskpath, category, excludes=None):
    excludes = excludes or []
    logger.debug("sync_directories_from_fullfilelist %r" % diskpath)
    category.unreadable_dirs = set()
    # drop any trailing slashes from diskpath
    diskpath = diskpath.rstrip("/")

    seen = set()
    with open(diskpath + "/fullfilelist") as stream:
        for row in stream:
            row = os.path.dirname(os.path.join(diskpath, row.strip()))
            if os.path.splitext(row)[1]:
                # If there is an extension it's a file not a folder
                continue
            if row in seen:
                continue
            seen.add(row)
            relativeDName = os.path.join(diskpath, row).replace(config["UMDL_PREFIX"], "")
            relativeDName = relativeDName.rstrip("/")
            logger.debug("  walking %r" % relativeDName)
            if is_excluded(relativeDName, stdexcludes + excludes):
                logger.info("excluding %s" % (relativeDName))
                continue

            # avoid disappearing directories
            try:
                s = os.stat(os.path.join(config["UMDL_PREFIX"], relativeDName))
                ctime = s[stat.ST_CTIME]
            except OSError:
                logger.debug("Avoiding %r, dissappeared." % relativeDName)
                continue

            mode = s.st_mode
            readable = not not (mode & stat.S_IRWXO & (stat.S_IROTH | stat.S_IXOTH))
            if not readable or umdl.parent_dir(relativeDName) in category.unreadable_dirs:
                category.unreadable_dirs.add(relativeDName)

            umdl.sync_category_directory(session, config, category, relativeDName, readable, ctime)
            session.commit()


def sync_directories_from_disk(session, config, diskpath, category, excludes=None):
    excludes = excludes or []
    logger.debug("sync_directories_from_disk %r" % diskpath)
    category.unreadable_dirs = set()
    # drop any trailing slashes from diskpath
    diskpath = diskpath.rstrip("/")

    for dirpath, _dirnames, _filenames in os.walk(diskpath, topdown=True):
        relativeDName = dirpath.replace(config["UMDL_PREFIX"], "")
        logger.debug("  walking %r" % relativeDName)

        if is_excluded(relativeDName, stdexcludes + excludes):
            logger.info("excluding %s" % (relativeDName))
            continue

        # avoid disappearing directories
        try:
            s = os.stat(os.path.join(config["UMDL_PREFIX"], relativeDName))
            ctime = s[stat.ST_CTIME]
        except OSError:
            logger.debug("Avoiding %r, dissappeared." % relativeDName)
            continue

        mode = s.st_mode
        readable = not not (mode & stat.S_IRWXO & (stat.S_IROTH | stat.S_IXOTH))
        if not readable or umdl.parent_dir(relativeDName) in category.unreadable_dirs:
            category.unreadable_dirs.add(relativeDName)

        umdl.sync_category_directory(session, config, category, relativeDName, readable, ctime)
    session.commit()


def setup_logging(config, logfile, debug, list_categories):
    log_dir = config.get("MM_LOG_DIR", None)
    # check if the directory exists
    if log_dir is not None:
        if not os.path.isdir(log_dir):
            # MM_LOG_DIR seems to be configured but does not exist
            # Logging into cwd.
            logger.warning("Directory " + log_dir + " does not exists." " Logging into CWD.")
            log_dir = None

    if log_dir is not None:
        log_file = log_dir + "/" + logfile
    else:
        log_file = logfile

    fmt = "%(asctime)s %(message)s"
    datefmt = "%m/%d/%Y %I:%M:%S %p"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    handler = logging.handlers.WatchedFileHandler(log_file, "a+b")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # list_categories is a special case where the user wants to see something
    # on the console and not only in the log file
    if debug or list_categories:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
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
@click.option("--logfile", type=click.Path(), default="umdl.log", help="write logs to PATH")
@click.option(
    "--list",
    "list_categories",
    is_flag=True,
    default=False,
    help="list existing categories and exit",
)
@click.option(
    "--category",
    "categories",
    metavar="CATEGORY",
    default=None,
    help="only scan category CATEGORY",
)
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
@click.option(
    "--delete-directories",
    is_flag=True,
    default=False,
    help="delete directories from the database that are no longer on disk",
)
@click.option("--start-at", "path", default=None, help="Specify the path at which to start the run")
def main(config, logfile, list_categories, categories, debug, delete_directories, path):
    warnings.warn(
        "This command is deprecated and will be removed in the next version. "
        "To my knowledge, it's a rewrite that has never actually been used. "
        "Please open a ticket at https://github.com/fedora-infra/mirrormanager2/issues "
        "if you still need it.",
        DeprecationWarning,
        stacklevel=1,
    )
    config = read_config(config)
    db_manager = get_db_manager(config)
    session = db_manager.Session()

    setup_logging(config, logfile, debug, list_categories)

    logger.info("Starting umdl")

    if list_categories:
        categories = mirrormanager2.lib.get_categories(session)
        for c in categories:
            logger.info(c)
        session.close()
        logger.info("Ending umdl")
        return 0

    umdl.setup_arch_version_cache(session)
    check_categories = []
    if categories is None:
        check_categories = config.get("UMDL_MASTER_DIRECTORIES")
    else:
        for i in config.get("UMDL_MASTER_DIRECTORIES"):
            if i["category"] == categories:
                check_categories.append(i)

    for i in check_categories:
        cname = i["category"]

        category = mirrormanager2.lib.get_category_by_name(session, cname)
        if not category:
            logger.error(
                "UMDL_MASTER_DIRECTORIES Category %s does not exist in the "
                "database, skipping" % (cname)
            )
            continue

        if category.product is None:
            logger.error(
                "UMDL_MASTER_DIRECTORIES Category %s has null Product, " "skipping" % (cname)
            )
            continue

        category.excludes = i.get("excludes", [])
        category.extra_rsync_options = i.get("options")
        category.directory_cache = cache_directories(category)

        category_path = i["path"]
        if len(check_categories) == 1:
            category_path = path or i["path"]

        if i["type"] == "directory":
            # import cProfile, pstats, StringIO
            # pr = cProfile.Profile()
            # pr.enable()
            sync_directories_from_disk(session, config, category_path, category)
            # pr.disable()

            # s = StringIO.StringIO()
            # sortby = 'cumulative'
            # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            # ps.print_stats(.1)
            # print s.getvalue()
        elif i["type"] == "fullfilelist":
            # import cProfile, pstats, StringIO
            # pr = cProfile.Profile()
            # pr.enable()
            sync_directories_from_fullfilelist(session, config, category_path, category)
            # pr.disable()

            # s = StringIO.StringIO()
            # sortby = 'cumulative'
            # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            # ps.print_stats(.1)
            # print s.getvalue()
        else:
            logger.info("Un-supported type: %s" % i["type"])

    logger.info("Refresh the list of repomd.xml")
    Directory.age_file_details(session, config)

    logger.info("Ending umdl")
