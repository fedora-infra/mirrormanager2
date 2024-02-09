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
summary file), it will create a repository object (cf `umdl.RepoMaker`) which
is basically a mapping between a yum repo name (ie: Fedora-20-updates) and a
directory (/pub/fedora/linux/updates/....)

"""

import datetime
import glob
import logging
import logging.handlers
import mmap
import os
import re
import stat
import time
from contextlib import contextmanager
from functools import partial

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

import mirrormanager2.lib
import mirrormanager2.lib.umdl as umdl
from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import Directory
from mirrormanager2.lib.sync import run_rsync

from .common import get_filtered_categories, read_config

STD_EXCLUDES = [r".*\.snapshot", r".*/\.~tmp~"]
# This directories will be skipped during repository creation
# This should leave 'Everything' as the directory which is used to create the repository.
SKIP_REPO_DIRS = ["Cloud", "Workstation", "Server"]


logger = logging.getLogger("umdl")
_current_cname = "N/A"


class MasterFilter(logging.Filter):
    def filter(self, record):
        record.category = _current_cname
        return True


def is_excluded(path, excludes):
    for e in excludes:
        if re.compile(e).match(path):
            return True
    return False


def ctime_from_rsync(date, hms):
    year, month, day = date.split("/")
    hour, minute, second = hms.split(":")
    t = datetime.datetime(
        int(year), int(month), int(day), int(hour), int(minute), int(second), 0, None
    )
    return int(time.mktime(t.timetuple()))


def short_filelist(files):
    html = 0
    rpms = 0
    hdrs = 0
    drpms = 0
    for f in files.keys():
        if f.endswith(".html"):
            html += 1
        if f.endswith(".rpm"):
            rpms += 1
        if f.endswith(".hdr"):
            hdrs += 1
        if f.endswith(".drpm"):
            drpms += 1
    if html > 10 or rpms > 10 or hdrs > 10 or drpms > 10:
        date_file_list = []
        rc = {}
        for k in files.keys():
            date_file_tuple = (files[k]["stat"], k, files[k]["size"])
            date_file_list.append(date_file_tuple)
        date_file_list.sort()
        # keep the most recent 3
        date_file_list = date_file_list[-3:]

        for _, k, _ in date_file_list:
            rc[k] = files[k]
        return rc
    else:
        return files


# def sync_category_directory(session, config, category, relativeDName, ctime, files, is_repo):
#     """
#     This function is a re-implementation of the function
#     sync_directories() using fullfiletimelist and (almost)
#     no disk access. It checks if the directory :relativeDName: has
#     a newer :ctime: than in the database. If it does it updates the
#     directory information in the database. Including checksums and
#     repository metadata (for metalinks).

#     :param session: SQLAlchemy session
#     :param config: umdl config
#     :param category: SQLAlchemy object of a MirrorManager category
#     :param relativeDName: current directory name
#     :param ctime: actual ctime from relativeDName
#     :param files: contains file-names, ctimes and sizes of all
#                   files in the directory relativeDName
#     :param is_repo: this boolean is true if the current directory
#                     :relativeDName: has a 'repodata'
#                     sub-directory.
#     """

#     logger.debug(f"  sync_category_directory {category} - {relativeDName}")

#     topdir = category.topdir.name

#     created = False
#     set_ctime = False
#     relativeDName = relativeDName.replace(topdir, "")
#     if relativeDName.startswith("/"):
#         relativeDName = relativeDName[1:]
#     if relativeDName in category.directory_cache:
#         d = category.directory_cache[relativeDName]
#         if d["ctime"] != ctime:
#             set_ctime = True
#             logger.info(
#                 "ctime changed for %s: ctime in database: %d "
#                 "- ctime on disk: %d" % (topdir + "/" + relativeDName, d["ctime"], ctime)
#             )
#         D = mirrormanager2.lib.get_directory_by_id(session, d.id)
#     else:
#         if relativeDName == "":
#             D = category.topdir
#         else:
#             # Can't find the new directory, just add it
#             dname = os.path.join(topdir, relativeDName)
#             D = Directory(name=dname, ctime=ctime)
#             logger.debug(f"Created Directory({dname}, ctime={ctime})")
#             created = True
#         # Add this category to the directory
#         D.categories.append(category)
#         session.add(D)
#         # And flush so that we can already start using it
#         session.flush()
#         # Refresh the cache
#         category.directory_cache[relativeDName] = D

#     if set_ctime:
#         D.ctime = ctime

#     if set_ctime or created:
#         # stating changed files to see if they are readable
#         s = None
#         try:
#             s = os.stat(os.path.join(config["UMDL_PREFIX"], topdir, relativeDName))
#         except OSError:
#             # The main reason for this execption is that the
#             # file from the fullfiletimelist does not exist.
#             logger.warning(
#                 "Hmm, stat()ing %s failed. Theoretically this cannot happen." % relativeDName
#             )

#         if s:
#             mode = s.st_mode
#             D.readable = not not (mode & stat.S_IRWXO & (stat.S_IROTH | stat.S_IXOTH))
#         # the whole stat block can be removed once fullfiletimelist marks unreadable directories

#         shortfiles = short_filelist(files)
#         if D.files != shortfiles:
#             D.files = shortfiles
#             logger.debug(f"File list for directory {relativeDName} updated: {D.files}")
#         session.add(D)
#         session.flush()

#         # Having the checksum detection here means, that only checksums of
#         # new or changed directories will be picked up.
#         # As the checksums detection code was broken for some time, not all
#         # missing checksums will be picked up in fullfiletimelist mode.
#         # The actual disk scanning will find those files, however.
#         loader = umdl.FileDetailFromChecksumsListLoader(session, config, D, files)
#         loader.load()

#     if is_repo and (set_ctime or created):
#         # This is here to skip MM repository creation for those
#         # directories. This should leave 'Everything' as the directory
#         # which is used to create the repository.
#         # This is not the most flexible implementation.

#         skip_dir = ["Cloud", "Workstation", "Server"]
#         if not any(x in relativeDName for x in skip_dir):
#             repomaker = umdl.RepoMaker(session, config)
#             repomaker.make(D, relativeDName, category, "repomd.xml")

#     if ("repomd.xml" in files) and (set_ctime or created):
#         diskpath = os.path.join(config["UMDL_PREFIX"], category.topdir.name)
#         umdl.make_repo_file_details(session, diskpath, relativeDName, D, "repomd.xml")


class SyncImpossible(Exception):
    pass


class DirSynchronizer:
    def __init__(self, session, config, category, path, excludes=None):
        self.session = session
        self.config = config
        self.category = category
        # drop any trailing slashes from path
        self.path = path.rstrip("/")
        self.excludes = excludes or []
        self.make_repo_file_details = True
        self.progress_bar = None

    def _get_category_directories(self, **kwargs):
        raise NotImplementedError

    def sync(self, **kwargs):
        category_directories = self._get_category_directories(**kwargs)
        self.sync_directories(category_directories)
        self.sync_repos(category_directories)

    def _get_relative_name(self, directory):
        topdirName = self.category.topdir.name
        return directory.name[len(topdirName) + 1 :]

    def _is_dir_gone(self, d, **kwargs):
        relativeDName = self._get_relative_name(d)
        return not os.path.isdir(os.path.join(self.path, relativeDName))

    def nuke_gone_directories(self, **kwargs):
        """deleting a Directory has a ripple effect through the whole
        database.  Be really sure you're ready do to this.  It comes
        in handy when say a Test release is dropped."""
        directories = self.category.directories  # in ascending name order
        directories.reverse()  # now in descending name order, bottoms up
        for d in directories:
            if is_excluded(d.name, self.excludes):
                continue
            gone = self._is_dir_gone(d, **kwargs)
            if gone and len(d.categories) == 1:  # safety, this should always trigger
                logger.info("Deleting gone directory %s" % (d.name))
                self.session.delete(d)
                self.session.flush()

    def sync_directories(self, category_directories):
        logger.debug("  sync_directories %s", self.category)
        if self.progress_bar is not None:
            self.progress_bar.reset(
                description=f"Syncing directories of {self.category.name}",
                total=len(category_directories),
            )

        for relativeDName in sorted(category_directories.keys()):
            value = category_directories[relativeDName]
            set_readable = False
            set_ctime = False
            set_files = False

            if self.progress_bar is not None:
                self.progress_bar.advance()

            if relativeDName in self.category.directory_cache:
                d = self.category.directory_cache[relativeDName]
                if value["readable"] is not None and d.readable != value["readable"]:
                    set_readable = True
                if d.ctime != value["ctime"]:
                    set_ctime = True
                D = mirrormanager2.lib.get_directory_by_id(self.session, d.id)
            else:
                if relativeDName == "":
                    D = self.category.topdir
                else:
                    # Can't find the new directory, just add it
                    dname = os.path.join(self.category.topdir.name, relativeDName)
                    D = Directory(name=dname, readable=value["readable"], ctime=value["ctime"])
                    logger.debug(
                        "Created Directory({}, readable={}, ctime={})".format(
                            dname, value["readable"], value["ctime"]
                        )
                    )
                # Add this category to the directory
                D.categories.append(self.category)
                self.session.add(D)
                # And flush so that we can already start using it
                self.session.flush()
                # Refresh the cache
                self.category.directory_cache_clear()
                d = self.category.directory_cache[relativeDName]

            if value["changed"]:
                set_files = True

            if set_readable:
                D.readable = value["readable"]
            if set_ctime:
                D.ctime = value["ctime"]
            if set_files:
                short_fl = short_filelist(value["files"])
                if D.files != short_fl:
                    D.files = short_fl
            self.session.add(D)
            self.session.flush()
            loader = umdl.FileDetailFromChecksumsLoader(self.session, self.config, D)
            loader.load()

    def sync_repos(self, category_directories):
        if self.progress_bar is not None:
            self.progress_bar.reset(
                description=f"Syncing repositories of {self.category.name}",
                total=len(category_directories),
            )
        # this has to be a done after sync_directories to be sure the child repodata/
        # dir is created in the db first
        repomaker = umdl.RepoMaker(self.session, self.config)

        for relativeDName, data in category_directories.items():
            if self.progress_bar is not None:
                self.progress_bar.advance()

            D = self.category.directory_cache[relativeDName]
            # D = mirrormanager2.lib.get_directory_by_id(self.session, d.id)

            if (data["isRepository"] or data["isAtomic"]) and not any(
                srd in relativeDName for srd in SKIP_REPO_DIRS
            ):
                if data["isRepository"]:
                    target = "repomd.xml"
                elif data["isAtomic"]:
                    target = "summary"
                repomaker.make_repo(D, relativeDName, self.category, target)

            for target in ("repomd.xml", "summary"):
                if target in data["files"] and self.make_repo_file_details:
                    repomaker.make_file_details(D, self.path, relativeDName, target)


class RsyncDirSynchronizer(DirSynchronizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_repo_file_details = False  # ab: not sure why

    @contextmanager
    def _get_rsync_listing(self, extra_rsync_options=None):
        try:
            result, output = run_rsync(self.path, extra_rsync_options, logger)
        except Exception:
            logger.warning("Failed to run rsync.", exc_info=True)
            return
        if result > 0:
            logger.info(
                "rsync returned exit code %s for Category %s: %s",
                result,
                self.category.name,
                output,
            )
        # still, try to use the output listing if we can
        yield output

    def _get_category_directories(self, **kwargs):
        with self._get_rsync_listing(**kwargs) as output:
            return self.parse_rsync_listing(output)

    def fill_category_directories_from_rsync(self, line, category_directories, unreadable_dirs):
        topdirName = self.category.topdir.name
        readable = True
        relativeDName = line.split()[4]
        # if re.compile(r"^\.$").match(relativeDName):
        if relativeDName == ".":
            directoryname = topdirName
        else:
            directoryname = os.path.join(topdirName, relativeDName)

        if is_excluded(directoryname, STD_EXCLUDES + self.excludes):
            return

        perms = line.split()[0]
        if (
            not re.compile("^d......r.x").match(perms)
            or umdl.parent_dir(relativeDName) in unreadable_dirs
        ):
            readable = False
            unreadable_dirs.add(relativeDName)

        try:
            perm, size, date, hms, filepath = line.split()
        except ValueError:
            raise
        ctime = ctime_from_rsync(date, hms)

        category_directories[relativeDName] = {
            "files": {},
            "isRepository": False,
            "isAtomic": False,
            "readable": readable,
            "ctime": ctime,
            "changed": True,
        }
        if relativeDName.endswith("repodata"):
            parent_relativeDName = umdl.parent_dir(relativeDName)
            try:
                category_directories[parent_relativeDName]["isRepository"] = True
            except KeyError:
                category_directories[parent_relativeDName] = {
                    "files": {},
                    "isRepository": True,
                    "readable": readable,
                    "ctime": ctime,
                    "changed": True,
                }

        return category_directories

    def add_file_to_directory(self, line, category_directories):
        try:
            perm, size, date, hms, filepath = line.split()
        except ValueError:
            return
        try:
            dt = ctime_from_rsync(date, hms)
        except ValueError:
            return

        splittedpath = filepath.split("/")
        filename = splittedpath[-1]
        subpath = splittedpath[:-1]
        if len(subpath) > 0:
            relativeDName = os.path.join(*subpath)
        else:
            relativeDName = ""
        category_directories[relativeDName]["files"][filename] = {"size": size, "stat": dt}

    def parse_rsync_listing(self, f):
        category_directories = {}
        unreadable_dirs = set()
        for line in f:
            line.strip()
            splittedline = line.split()
            if line.startswith("d") and len(splittedline) == 5 and len(splittedline[0]) == 10:
                # good guess it's a directory line
                if re.compile(r"^\.$").match(line):
                    # we know category.topdir exists and isn't excluded
                    pass
                else:
                    category_directories = self.fill_category_directories_from_rsync(
                        line, category_directories, unreadable_dirs
                    )
            else:
                self.add_file_to_directory(line, category_directories)
        return category_directories


class FileDirSynchronizer(RsyncDirSynchronizer):
    @contextmanager
    def _get_rsync_listing(self, path, category):
        with open(path) as f:
            yield f


class DiskDirSynchronizer(DirSynchronizer):
    def _get_category_directories(self, **kwargs):
        logger.debug("sync_directories_from_disk %r", self.path)
        unreadable_dirs = set()
        category_directories = {}

        for dirpath, dirnames, filenames in os.walk(self.path, topdown=True):
            relativeDName = dirpath[len(self.path) + 1 :]
            relativeDName = relativeDName.strip("/")
            logger.debug("  walking %r", relativeDName)
            if is_excluded(relativeDName, STD_EXCLUDES):
                logger.info("excluding %s", relativeDName)
                # exclude all its subdirs too
                dirnames[:] = []
                continue

            # avoid disappearing directories
            try:
                s = os.stat(os.path.join(self.path, relativeDName))
                ctime = s[stat.ST_CTIME]
            except OSError:
                logger.debug("Avoiding %r, dissappeared." % relativeDName)
                continue

            try:
                d_ctime = self.category.directory_cache[relativeDName].ctime
            except KeyError:
                # we'll need to create it
                d_ctime = 0

            # dirnames.sort()

            readable = bool(s.st_mode & stat.S_IRWXO & (stat.S_IROTH | stat.S_IXOTH))
            if not readable or umdl.parent_dir(relativeDName) in unreadable_dirs:
                unreadable_dirs.add(relativeDName)
            isRepo = "repodata" in dirnames
            isAtomic = "summary" in filenames and "objects" in dirnames

            changed = d_ctime != ctime
            if changed:
                logger.info(f"{relativeDName} has changed: {d_ctime} != {ctime}")
            else:
                logger.debug("    %s has not changed" % relativeDName)

            category_directories[relativeDName] = {
                "files": {},
                "isRepository": isRepo,
                "isAtomic": isAtomic,
                "readable": readable,
                "ctime": ctime,
                "changed": changed,
            }

            # skip per-file stat()s if the directory hasn't changed
            if changed:
                for f in filenames:
                    try:
                        s = os.stat(os.path.join(self.path, relativeDName, f))
                    except OSError:
                        continue
                    category_directories[relativeDName]["files"][f] = {
                        "size": str(s.st_size),
                        "stat": s[stat.ST_CTIME],
                    }

        return category_directories


class FFTDirSynchronizer(DirSynchronizer):
    def _is_dir_gone(self, d, ctimes):
        if d.name == self.category.topdir.name:
            return False
        return d.name not in ctimes

    def _parse_fullfiletimelist(self):
        """
        This functions tries to scan the master mirror by looking for
        'fullfiletimelist-*' and using its content instead of accessing
        the file-system. This greatly speeds up master mirror scanning
        and reduces overall I/O on the storage system.
        If no 'fullfiletimelist-*' file is found the functions raises
        SyncImpossible and umdl can fall back to disk based master mirror
        scanning.

        :param session: SQLAlchemy session
        :param config: umdl config
        :param path: top directory of the category where the
                        master mirror scanning starts
        :param category: SQLAlchemy object of a MirrorManager category
        :raises: SyncImpossible if the file was not found
        """

        def _handle_fedora_linux_category(p):
            if self.category.name == "Fedora Linux":
                # The 'Fedora Linux' category is the only category
                # which starts at one directory level lower.
                # 'Fedora Linux' -> pub/fedora/linux
                # 'Fedora EPEL' -> pub/epel
                # fullfiletimelist-fedora starts at linux/
                # need to remove 'linux/' so that topdir + filename
                # point to the right file
                return p[6:]
            return p

        # let's look for a fullfiletimelist-* file
        try:
            if self.category.name == "Fedora Linux":
                filelist = glob.glob(f"{self.path}/../fullfiletimelist-*")
            else:
                filelist = glob.glob(f"{self.path}/fullfiletimelist-*")
        except Exception as e:
            raise SyncImpossible from e

        if len(filelist) < 1:
            # not a single element found in the glob
            raise SyncImpossible

        # blindly take the first file found by the glob
        logger.info("Loading and parsing %s", filelist[0])

        if self.progress_bar is not None:
            self.progress_bar.reset(
                description=f"Reading fullfiletimelist of {self.category.name}", total=None
            )

        # A hash with directories as key and ctime as value
        ctimes = {}
        # A hash with directories as key and
        # { filename: { 'stat' : ctime, 'size': 'filesize' } } as value
        files = {}
        seen = set()
        # A set with a list of directories with a repository (repodata)
        repo = set()
        # These two sets will be used to determine if it's an atomic repo dir.
        # An atomic repo dir has both a summary file and an objects dir
        has_summary = set()
        has_objects = set()

        umdl_prefix = self.config["UMDL_PREFIX"]
        # Not opening the file as stream and reading line by line as this breaks
        # if the file changes. As this can happen, the file is loaded once into
        # memory using mmap.
        with open(filelist[0], "rb") as f:
            # tell mmap to open file read-only or mmap might fail
            m = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
            row = m.readline()
            while row:
                row = row.decode()
                col = row.strip().split("\t")
                row = m.readline()
                # only rows with at least 4 columns are what we are looking for
                # 'ctime\ttype\tsize\tname'
                if len(col) < 4:
                    continue
                # Type can be either 'f', 'd', 'f-', 'd-'.
                # As long as the '-' support is not implemented only look
                # for the first character so that this does not break
                # once types with '-' can appear.
                # https://pagure.io/quick-fedora-mirror/issue/40

                # only files (type: f)
                if col[1][0] == "f":
                    # put all the information in a dict with path as key
                    tmp = os.path.dirname(_handle_fedora_linux_category(col[3]))
                    tmp = os.path.join(self.path, tmp).replace(umdl_prefix, "")
                    tmp2 = os.path.basename(_handle_fedora_linux_category(col[3]))

                    if tmp in seen:
                        files[tmp].update({tmp2: {"stat": int(col[0]), "size": col[2]}})
                    else:
                        files[tmp] = {tmp2: {"stat": int(col[0]), "size": col[2]}}
                        # Use a set() to track if the element already exists in the dict().
                        # This is much faster than if tmp in files.keys(); much much faster
                        seen.add(tmp)
                    if tmp2 == "summary":
                        # There is a 'summary' file, add the parent
                        # directory to the has_summary set().
                        has_objects.add(tmp)
                elif col[1][0] == "d":
                    # get all directories and their ctime
                    tmp = os.path.join(self.path, _handle_fedora_linux_category(col[3]))

                    tmp = tmp.replace(umdl_prefix, "")
                    ctimes[tmp] = int(col[0])
                    # Only if a directory contains a 'repodata' directory
                    # it should be used for repository creation.
                    if "repodata" in tmp:
                        # There is a 'repodata' directory, add the parent
                        # directory to the repo set().
                        # Remove '/repodata'
                        repo.add(tmp[:-9])
                    if tmp.endswith("objects"):
                        # There is a 'repodata' directory, add the parent
                        # directory to the has_objects set().
                        # Remove '/objects'
                        has_objects.add(tmp[:-8])

        # add the root directory of the current category
        tmp = self.path.replace(umdl_prefix, "")
        ctimes[tmp] = 0
        return {
            "ctimes": ctimes,
            "files": files,
            "repo_dirs": repo,
            "atomic_dirs": has_summary & has_objects,
        }

    def _get_category_directories(self, **kwargs):
        data = self._parse_fullfiletimelist()

        logger.debug("sync_directories_from_fullfiletimelist %s", self.path)

        if self.progress_bar is not None:
            self.progress_bar.reset(
                description=f"Building directory statuses of {self.category.name}", total=None
            )

        seen = set()

        category_directories = {}
        for dirname in data["ctimes"].keys():
            if dirname in seen:
                logger.info("Skipping already seen directory %s", dirname)
                continue
            seen.add(dirname)
            if is_excluded(dirname, STD_EXCLUDES):
                logger.info("Excluding %s" % (dirname))
                continue
            try:
                file_dict = data["files"][dirname]
            except Exception:
                # An empty directory is not part of files{}
                file_dict = {}

            relativeDName = dirname.replace(self.category.topdir.name, "")
            if relativeDName.startswith("/"):
                relativeDName = relativeDName[1:]

            try:
                db_ctime = self.category.directory_cache[relativeDName].ctime
            except KeyError:
                # we'll need to create it
                db_ctime = 0

            is_repo = dirname in data["repo_dirs"]
            is_atomic = dirname in data["atomic_dirs"]
            ctime = data["ctimes"][dirname]
            changed = db_ctime != ctime
            readable = None
            if changed:
                try:
                    fullpath = os.path.join(self.config["UMDL_PREFIX"], dirname)
                    s = os.stat(fullpath)
                except OSError as e:
                    # The main reason for this execption is that the
                    # file from the fullfiletimelist does not exist.
                    logger.warning(
                        "Hmm, stat()ing %s failed. Theoretically this cannot happen. %s",
                        fullpath,
                        e,
                    )
                else:
                    readable = bool(s.st_mode & stat.S_IRWXO & (stat.S_IROTH | stat.S_IXOTH))
                # the whole stat block can be removed once fullfiletimelist marks unreadable
                # directories

            category_directories[relativeDName] = {
                "files": file_dict,
                "isRepository": is_repo,
                "isAtomic": is_atomic,
                "readable": readable,
                "ctime": ctime,
                "changed": changed,
            }

        return category_directories


def setup_logging(config, debug, logfile, console):
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

    fmt = "%(asctime)s : %(category)s : %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    handler = logging.handlers.WatchedFileHandler(log_file, "a+")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    f = MasterFilter()
    logger.addFilter(f)
    # list_categories is a special case where the user wants to see something
    # on the console and not only in the log file
    if debug:
        handler = RichHandler(console=console, rich_tracebacks=True)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


class ProgressBar:
    def __init__(self, progress):
        self.progress = progress
        self.task_id = progress.add_task("Processing")

    def __getattr__(self, name):
        return partial(getattr(self.progress, name), self.task_id)


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
    "only_category",
    metavar="CATEGORY",
    default=None,
    help="only scan category CATEGORY",
)
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
@click.option(
    "--skip-fullfiletimelist",
    is_flag=True,
    default=False,
    help="Do not look for a fullfiletimelist-*; actually scan the filesystem",
)
@click.option(
    "--delete-directories",
    is_flag=True,
    default=False,
    help="delete directories from the database that are no longer on disk",
)
def main(
    config,
    logfile,
    list_categories,
    only_category,
    debug,
    skip_fullfiletimelist,
    delete_directories,
):
    global _current_cname
    config = read_config(config)
    db_manager = get_db_manager(config)
    console = Console()

    setup_logging(config, debug or list_categories, logfile, console)

    if list_categories:
        with db_manager.Session() as session:
            categories = mirrormanager2.lib.get_categories(session)
            for c in categories:
                logger.info(c)
        return 0

    logger.info("Starting umdl")
    with db_manager.Session() as session:
        check_categories = get_filtered_categories(config, session, only_category)
        with Progress(console=console, refresh_per_second=2) as progress:
            progress_bar = ProgressBar(progress)
            for master_dir in check_categories:
                check_category(
                    config,
                    session,
                    master_dir,
                    delete_directories,
                    skip_fullfiletimelist,
                    progress_bar,
                )

        logger.debug("Refresh the list of repomd.xml")
        Directory.age_file_details(session, config)
        session.commit()

    _current_cname = "N/A"
    logger.info("Ending umdl")


def check_category(
    config, session, master_dir, delete_directories, skip_fullfiletimelist, progress_bar
):
    global _current_cname
    _current_cname = master_dir["category"]
    # category = mirrormanager2.lib.get_category_by_name(session, cname)
    category = master_dir["category_db"]

    if master_dir["type"] in ("rsync", "file"):
        if master_dir["type"] == "rsync":
            syncer_classes = [RsyncDirSynchronizer]
        elif master_dir["type"] == "file":
            syncer_classes = [FileDirSynchronizer]
        path = master_dir["url"]
        extra_args = {"extra_rsync_options": master_dir.get("options")}
    if master_dir["type"] == "directory":
        syncer_classes = [DiskDirSynchronizer]
        if not skip_fullfiletimelist:
            syncer_classes.insert(0, FFTDirSynchronizer)
        path = master_dir["path"]
        extra_args = {}
    # Now run the sync using the corresponding methods
    for syncer_class in syncer_classes:
        syncer = syncer_class(
            session,
            config,
            category,
            path,
            excludes=master_dir.get("excludes"),
        )
        syncer.progress_bar = progress_bar
        progress_bar.reset()
        try:
            syncer.sync(**extra_args)
            if delete_directories and master_dir["type"] != "rsync":  # Why not rsync?
                syncer.nuke_gone_directories()
        except SyncImpossible:
            continue
        break
