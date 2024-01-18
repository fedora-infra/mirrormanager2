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

import datetime
import glob
import hashlib
import logging
import logging.handlers
import mmap
import os
import re
import stat
import time

import click
import rpmmd.repoMDObject

import mirrormanager2.lib
import mirrormanager2.lib.umdl as umdl
from mirrormanager2.lib.database import get_db_manager
from mirrormanager2.lib.model import Directory, FileDetail, Repository
from mirrormanager2.lib.repomap import repo_prefix
from mirrormanager2.lib.sync import run_rsync

from .common import read_config

logger = logging.getLogger("umdl")
stdexcludes = [r".*\.snapshot", r".*/\.~tmp~"]
cname = "N/A"


class MasterFilter(logging.Filter):
    def filter(self, record):
        record.category = cname
        return True


def make_file_details_from_checksums(session, config, D, files=None):
    """
    This function looks for checksum files in the given directory. From those
    checksum files the checksums are extracted and then written to
    MirrorManager's database. With the checksums in the database
    MirrorManager can create metalinks for those files, ISOs for example.

    If the variable :files: is None this function will actually access the
    file-system to detect if the checksum files exits. If :files: is not None
    the function will use files to detect if checksum files exist.

    :param session: SQLAlchemy session
    :param config: umdl config
    :param D: MirrorManager database directory object
    :param files: optional hash with the files in the directory; if this is
                  None, the function will actually scan the directory :D:
    """

    def _handle_checksum_line(line, checksumlen):
        """
        This function tries to extract the filename and the its checksum
        from given :line:.
        """

        line = line.strip().split()
        if len(line) == 2:
            # old style fileformat
            # 25ceb179396f455836481a5b340bc24073f8178546b1e51b *Fedora-i386-20-20131211.1-sda.qcow2
            checksum, filename = line
            algo, delimiter = None, None
        elif len(line) == 4:
            # new style - bsd style checksum
            # SHA256 (Fedora-Cloud-Base-25-1.3.x86_64.qcow2) = 4942be5d49c603d7cabb0394bb1a790eb336
            algo, filename, delimiter, checksum = line
        else:
            # this is a line we do not care about
            return None, None

        if algo is None:
            # old style fileformat
            if len(checksum) != checksumlen:
                return None, None
            # strip off extraneous starting '*' char from name
            filename = filename.lstrip("*")
            return filename, checksum

        # new style - bsd style checksum
        if (checksumlen == 32) and (algo != "MD5"):
            return None, None
        if (checksumlen == 40) and (algo != "SHA1"):
            return None, None
        if (checksumlen == 64) and (algo != "SHA256"):
            return None, None
        if (checksumlen == 128) and (algo != "SHA512"):
            return None, None

        filename = filename[1:-1]

        return filename, checksum

    def _parse_checksum_file(relativeDName, checksumlen):
        r = {}
        try:
            with open(os.path.join(config["UMDL_PREFIX"], relativeDName)) as f:
                for line in f:
                    filename, checksum = _handle_checksum_line(line, checksumlen)
                    if filename is not None:
                        r[filename] = checksum
        except Exception:
            pass
        return r

    def _checksums_from_globs(relativeDName, globs, checksumlen):
        """
        Finds checksum files on disk (or from the filelist) and extracts
        the checksums and places the result in a dict[filename] = checksum.
        Finding the checksum files does a os.listdir() if the variable
        files is None.

        :param relativeDName: path to the directory (without category topdir)
        :param globs: possible patterns containing checksums
        :param checksumlen: number of characters the checksum has
        :returns: dict[filename] = checksum
        """

        d = {}
        checksum_files = []
        for g in globs:
            if files is not None:
                for f in files.keys():
                    if re.compile(g).match(f):
                        checksum_files.append(os.path.join(relativeDName, f))
            else:
                for f in os.listdir(os.path.join(config["UMDL_PREFIX"], relativeDName)):
                    if re.compile(g).match(f):
                        checksum_files.append(os.path.join(relativeDName, f))
        for f in checksum_files:
            d.update(_parse_checksum_file(f, checksumlen))
        return d

    sha1_globs = [r".*\.sha1sum", "SHA1SUM", "sha1sum.txt"]
    md5_globs = [r".*\.md5sum", "MD5SUM", "md5sum.txt"]
    sha256_globs = [".*-CHECKSUM", "sha256sum.txt"]
    sha512_globs = [r".*\.sha512sum", "SHA512SUM", "sha512sum.txt"]
    md5dict = _checksums_from_globs(D.name, md5_globs, 32)
    sha1dict = _checksums_from_globs(D.name, sha1_globs, 40)
    sha256dict = _checksums_from_globs(D.name, sha256_globs, 64)
    sha512dict = _checksums_from_globs(D.name, sha512_globs, 128)

    sum_files = set()
    for k in md5dict.keys():
        sum_files.add(k)
    for k in sha1dict.keys():
        sum_files.add(k)
    for k in sha256dict.keys():
        sum_files.add(k)
    for k in sha512dict.keys():
        sum_files.add(k)

    for f in sum_files:
        if files is not None:
            try:
                size = int(files[f]["size"])
                ctime = files[f]["stat"]
            except KeyError:
                # there are seldom cases where the CHECKSUM file
                # points to files in a sub-directory like
                # pxeboot/vmlinuz; ignore it for now
                continue
        else:
            try:
                s = os.stat(os.path.join(config["UMDL_PREFIX"], D.name, f))
            except OSError:
                # bail if the file doesn't actually exist
                continue
            size = s.st_size
            ctime = s[stat.ST_CTIME]
        sha1 = sha1dict.get(f)
        md5 = md5dict.get(f)
        sha256 = sha256dict.get(f)
        sha512 = sha512dict.get(f)

        fd = mirrormanager2.lib.get_file_detail(
            session,
            directory_id=D.id,
            filename=f,
            sha1=sha1,
            md5=md5,
            sha256=sha256,
            sha512=sha512,
            size=size,
            timestamp=ctime,
        )
        if not fd:
            fd = FileDetail(
                directory=D,
                filename=f,
                sha1=sha1,
                md5=md5,
                sha256=sha256,
                sha512=sha512,
                timestamp=ctime,
                size=size,
            )
            session.add(fd)
            session.commit()
            logger.debug("Added checksum for %s to database", f)


def make_repo_file_details(session, diskpath, relativeDName, D, category, target):
    warning = "Won't make repo file details"

    if diskpath is None:
        logger.warning("%s: diskpath is None" % warning)
        return

    # For yum repos and ostree repos
    allowed_targets = ["repomd.xml", "summary"]
    if target not in allowed_targets:
        logger.warning(f"{warning}: {target!r} not in {allowed_targets!r}")
        return

    absolutepath = os.path.join(diskpath, relativeDName, target)

    if not os.path.exists(absolutepath):
        logger.warning(f"{warning}: {absolutepath!r} does not exist")
        return

    try:
        f = open(absolutepath)
        contents = f.read()
        f.close()
    except Exception:
        return

    size = len(contents)
    contents = contents.encode("utf-8")
    md5 = hashlib.md5(contents).hexdigest()
    sha1 = hashlib.sha1(contents).hexdigest()
    sha256 = hashlib.sha256(contents).hexdigest()
    sha512 = hashlib.sha512(contents).hexdigest()

    if target == "repomd.xml":
        yumrepo = rpmmd.repoMDObject.RepoMD("repoid", absolutepath)
        if "timestamp" not in yumrepo.__dict__:
            umdl.set_repomd_timestamp(yumrepo)
        timestamp = yumrepo.timestamp
    elif target == "summary":
        # TODO -- ostree repos may have a timestamp in their summary file
        # someday.  for now, just use the system mtime.
        timestamp = os.path.getmtime(absolutepath)

    fd = mirrormanager2.lib.get_file_detail(
        session,
        directory_id=D.id,
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
            directory_id=D.id,
            filename=target,
            sha1=sha1,
            md5=md5,
            sha256=sha256,
            sha512=sha512,
            timestamp=timestamp,
            size=size,
        )
        logger.info(f"Updating FileDetail {fd!r}, {absolutepath!r}")
        session.add(fd)
        session.commit()


def make_repository(session, directory, relativeDName, category, target):
    warning = "Won't make repository object"

    # For yum repos and ostree repos
    allowed_targets = ["repomd.xml", "summary"]
    if target not in allowed_targets:
        logger.warning(f"{warning}: {target!r} not in {allowed_targets!r}")
        return

    if target == "repomd.xml":
        (ver, arch) = umdl.guess_ver_arch_from_path(session, category, relativeDName)
        if ver is None or arch is None:
            logger.warning(f"{warning}: could not guess version and arch {ver!r}, {arch!r}")
            return None
    elif target == "summary":
        # For ostree, we someday need to actually extract the arch information
        # from the ostree repo, but for now (F21 and F22) we will only be
        # shipping x86_64, so we hardcode that.  At present, it is not possible
        # to query an ostree repo for the arch information.  Bug walters about
        # this.
        arch = mirrormanager2.lib.get_arch_by_name(session, "x86_64")
        # Furthermore, we'll grab the version piece from the path which looks
        # like atomic/rawhide or atomic/21.
        ver = relativeDName.rstrip("/").split("/")[-1]
        ver = mirrormanager2.lib.get_version_by_name_version(session, category.product.name, ver)
        if ver is None:
            if not relativeDName.endswith("/"):
                relativeDName += "/"
            ver = umdl.create_version_from_path(session, category, relativeDName)
            session.add(ver)
            session.commit()
            umdl.version_cache.append(ver)

    # stop making duplicate Repository objects.
    if len(directory.repositories) > 0:
        logger.warning("%s: directory already has a repository" % (directory.name))
        return None

    repo = None
    prefix = repo_prefix(relativeDName, category, ver)
    repo = mirrormanager2.lib.get_repo_prefix_arch(session, prefix, arch.name)

    if not repo:
        # historically, Repository.name was a longer string with
        # product and category deliniations.  But we were getting
        # unique constraint conflicts once we started introducing
        # repositories under repositories.  And .name isn't used for
        # anything meaningful.  So simply have it match dir.name,
        # which can't conflict.
        repo = Repository(
            name=directory.name,
            category=category,
            version=ver,
            arch=arch,
            directory=directory,
            prefix=prefix,
        )
        logger.info(
            f"Created Repository(prefix={prefix}, version={ver.name}, arch={arch.name}, "
            f"category={category.name}) -> Directory {directory.name}"
        )
        session.add(repo)
        session.flush()
    else:
        if repo.prefix != prefix:
            repo.prefix = prefix

    return repo


def is_excluded(path, excludes):
    for e in excludes:
        if re.compile(e).match(path):
            return True
    return False


def nuke_gone_directories(session, diskpath, category, ctimes=None):
    """deleting a Directory has a ripple effect through the whole
    database.  Be really sure you're ready do to this.  It comes
    in handy when say a Test release is dropped."""

    topdirName = category.topdir.name

    directories = category.directories  # in ascending name order
    directories.reverse()  # now in descending name order, bottoms up
    for d in directories:
        if is_excluded(d.name, category.excludes):
            continue

        gone = False

        if diskpath:
            relativeDName = umdl.remove_category_topdir(topdirName, d.name)
            if not os.path.isdir(os.path.join(diskpath, relativeDName)):
                gone = True
        else:
            if d.name == topdirName:
                continue
            if d.name not in ctimes.keys():
                gone = True
        if gone and len(d.categories) == 1:  # safety, this should always trigger
            logger.info("Deleting gone directory %s" % (d.name))
            session.delete(d)
            session.commit()


def ctime_from_rsync(date, hms):
    year, month, day = date.split("/")
    hour, minute, second = hms.split(":")
    t = datetime.datetime(
        int(year), int(month), int(day), int(hour), int(minute), int(second), 0, None
    )
    return int(time.mktime(t.timetuple()))


def fill_category_directories_from_rsync(line, category, topdirName, category_directories):
    readable = True
    relativeDName = line.split()[4]
    if re.compile(r"^\.$").match(relativeDName):
        directoryname = topdirName
    else:
        directoryname = os.path.join(topdirName, relativeDName)

    if is_excluded(directoryname, stdexcludes + category.excludes):
        return

    perms = line.split()[0]
    if (
        not re.compile("^d......r.x").match(perms)
        or umdl.parent_dir(relativeDName) in category.unreadable_dirs
    ):
        readable = False
        category.unreadable_dirs.add(relativeDName)

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


def add_file_to_directory(line, category_directories):
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


def sync_category_directory(session, config, category, relativeDName, ctime, files, is_repo):
    """
    This function is a re-implementation of the function
    sync_category_directories() using fullfiletimelist and (almost)
    no disk access. It checks if the directory :relativeDName: has
    a newer :ctime: than in the database. If it does it updates the
    directory information in the database. Including checksums and
    repository metadata (for metalinks).

    :param session: SQLAlchemy session
    :param config: umdl config
    :param category: SQLAlchemy object of a MirrorManager category
    :param relativeDName: current directory name
    :param ctime: actual ctime from relativeDName
    :param files: contains file-names, ctimes and sizes of all
                  files in the directory relativeDName
    :param is_repo: this boolean is true if the current directory
                    :relativeDName: has a 'repodata'
                    sub-directory.
    """

    logger.debug(f"  sync_category_directory {category} - {relativeDName}")

    topdir = category.topdir.name

    created = False
    set_ctime = False
    relativeDName = relativeDName.replace(topdir, "")
    if relativeDName.startswith("/"):
        relativeDName = relativeDName[1:]
    if relativeDName in category.directory_cache:
        d = category.directory_cache[relativeDName]
        if d["ctime"] != ctime:
            set_ctime = True
            logger.info(
                "ctime changed for %s: ctime in database: %d "
                "- ctime on disk: %d" % (topdir + "/" + relativeDName, d["ctime"], ctime)
            )
        D = mirrormanager2.lib.get_directory_by_id(session, d.id)
    else:
        if relativeDName == "":
            D = category.topdir
        else:
            # Can't find the new directory, just add it
            dname = os.path.join(topdir, relativeDName)
            D = Directory(name=dname, ctime=ctime)
            logger.debug(f"Created Directory({dname}, ctime={ctime})")
            created = True
        # Add this category to the directory
        D.categories.append(category)
        session.add(D)
        # And flush so that we can already start using it
        session.flush()
        # Refresh the cache
        category.directory_cache[relativeDName] = D

    if set_ctime:
        D.ctime = ctime

    if set_ctime or created:
        # stating changed files to see if they are readable
        s = None
        try:
            s = os.stat(os.path.join(config["UMDL_PREFIX"], topdir, relativeDName))
        except OSError:
            # The main reason for this execption is that the
            # file from the fullfiletimelist does not exist.
            logger.warning(
                "Hmm, stat()ing %s failed. Theoretically this cannot happen." % relativeDName
            )

        if s:
            mode = s.st_mode
            D.readable = not not (mode & stat.S_IRWXO & (stat.S_IROTH | stat.S_IXOTH))
        # the whole stat block can be removed once fullfiletimelist marks unreadable directories

        shortfiles = short_filelist(files)
        if D.files != shortfiles:
            D.files = shortfiles
            logger.debug(f"File list for directory {relativeDName} updated: {D.files}")
        session.add(D)
        session.flush()

        # Having the checksum detection here means, that only checksums of
        # new or changed directories will be picked up.
        # As the checksums detection code was broken for some time, not all
        # missing checksums will be picked up in fullfiletimelist mode.
        # The actual disk scanning will find those files, however.
        make_file_details_from_checksums(session, config, D, files)

    if is_repo and (set_ctime or created):
        # This is here to skip MM repository creation for those
        # directories. This should leave 'Everything' as the directory
        # which is used to create the repository.
        # This is not the most flexible implementation.

        skip_dir = ["Cloud", "Workstation", "Server"]
        if not any(x in relativeDName for x in skip_dir):
            umdl.make_repository(session, D, relativeDName, category, "repomd.xml", config)

    if ("repomd.xml" in files) and (set_ctime or created):
        umdl.make_repo_file_details(session, config, relativeDName, D, category, "repomd.xml")


def sync_category_directories(session, config, diskpath, category, category_directories):
    logger.debug("  sync_directories_directories %r" % category)

    for relativeDName in sorted(category_directories.keys()):
        value = category_directories[relativeDName]
        set_readable = False
        set_ctime = False
        set_files = False

        if relativeDName in category.directory_cache:
            d = category.directory_cache[relativeDName]
            if d["readable"] != value["readable"]:
                set_readable = True
            if d["ctime"] != value["ctime"]:
                set_ctime = True
            D = mirrormanager2.lib.get_directory_by_id(session, d.id)
        else:
            if relativeDName == "":
                D = category.topdir
            else:
                # Can't find the new directory, just add it
                dname = os.path.join(category.topdir.name, relativeDName)
                D = Directory(name=dname, readable=value["readable"], ctime=value["ctime"])
                logger.debug(
                    "Created Directory({}, readable={}, ctime={})".format(
                        dname, value["readable"], value["ctime"]
                    )
                )
            # Add this category to the directory
            D.categories.append(category)
            session.add(D)
            # And flush so that we can already start using it
            session.flush()
            # Refresh the cache
            category.directory_cache = cache_directories(category)
            d = category.directory_cache[relativeDName]

        if value["changed"]:
            set_files = True

        if set_readable or set_ctime or set_files:
            if set_readable:
                D.readable = value["readable"]
            if set_ctime:
                D.ctime = value["ctime"]
            if set_files:
                if D.files != short_filelist(value["files"]):
                    D.files = short_filelist(value["files"])
        session.add(D)
        session.commit()
        make_file_details_from_checksums(session, config, D)

    # this has to be a second pass to be sure the child repodata/ dir is
    # created in the db first
    for relativeDName, value in category_directories.items():
        d = category.directory_cache[relativeDName]
        D = mirrormanager2.lib.get_directory_by_id(session, d.id)

        if value["isRepository"]:
            target = "repomd.xml"
        elif value["isAtomic"]:
            target = "summary"
        else:
            target = None

        if value["isRepository"] or value["isAtomic"]:
            make_repository(session, D, relativeDName, category, target)

        if "repomd.xml" in value["files"]:
            target = "repomd.xml"
        elif "summary" in value["files"]:
            target = "summary"
        else:
            continue

        make_repo_file_details(session, diskpath, relativeDName, D, category, target)


def parse_rsync_listing(session, config, category, f):
    topdirName = category.topdir.name
    category_directories = {}
    category.unreadable_dirs = set()
    while True:
        line = f.readline()
        if not line:
            break
        line.strip()
        splittedline = line.split()
        if line.startswith("d") and len(splittedline) == 5 and len(splittedline[0]) == 10:
            # good guess it's a directory line
            if re.compile(r"^\.$").match(line):
                # we know category.topdir exists and isn't excluded
                pass
            else:
                category_directories = fill_category_directories_from_rsync(
                    line, category, topdirName, category_directories
                )
        else:
            add_file_to_directory(line, category_directories)

    sync_category_directories(session, config, None, category, category_directories)


def sync_directories_using_rsync(session, config, rsyncpath, category):
    try:
        result, output = run_rsync(rsyncpath, category.extra_rsync_options, logger)
    except Exception:
        logger.warning("Failed to run rsync.", exc_info=True)
        return
    if result > 0:
        logger.info(
            "rsync returned exit code %d for Category %s: %s" % (result, category.name, output)
        )
    # still, try to use the output listing if we can
    parse_rsync_listing(session, config, category, output)


def sync_directories_from_file(session, config, filename, category):
    f = open(filename)
    parse_rsync_listing(session, config, None, category, f)
    f.close()


def cache_directories(category):
    cache = dict()
    topdirName = category.topdir.name
    for directory in list(category.directories):
        relativeDName = umdl.remove_category_topdir(topdirName, directory.name).strip("/")
        cache[relativeDName] = directory
    return cache


def sync_directories_from_disk(session, config, diskpath, category, excludes=None):
    excludes = excludes or []
    logger.debug("sync_directories_from_disk %r" % diskpath)
    category.unreadable_dirs = set()
    # drop any trailing slashes from diskpath
    diskpath = diskpath.rstrip("/")
    category_directories = {}

    for dirpath, dirnames, filenames in os.walk(diskpath, topdown=True):
        relativeDName = dirpath[len(diskpath) + 1 :]
        relativeDName = relativeDName.strip("/")
        logger.debug("  walking %r" % relativeDName)
        if is_excluded(relativeDName, stdexcludes + excludes):
            logger.info("excluding %s" % (relativeDName))
            # exclude all its subdirs too
            dirnames[:] = []
            continue

        # avoid disappearing directories
        try:
            s = os.stat(os.path.join(diskpath, relativeDName))
            ctime = s[stat.ST_CTIME]
        except OSError:
            logger.debug("Avoiding %r, dissappeared." % relativeDName)
            continue

        try:
            d_ctime = category.directory_cache[relativeDName]["ctime"]
        except KeyError:
            # we'll need to create it
            d_ctime = 0

        dirnames.sort()

        mode = s.st_mode
        readable = not not (mode & stat.S_IRWXO & (stat.S_IROTH | stat.S_IXOTH))
        if not readable or umdl.parent_dir(relativeDName) in category.unreadable_dirs:
            category.unreadable_dirs.add(relativeDName)
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
                    s = os.stat(os.path.join(diskpath, relativeDName, f))
                except OSError:
                    continue
                category_directories[relativeDName]["files"][f] = {
                    "size": str(s.st_size),
                    "stat": s[stat.ST_CTIME],
                }

    sync_category_directories(session, config, diskpath, category, category_directories)

    if category.delete_directories:
        nuke_gone_directories(session, diskpath, category)


def sync_directories_from_fullfiletimelist(session, config, diskpath, category):
    """
    This functions tries to scan the master mirror by looking for
    'fullfiletimelist-*' and using its content instead of accessing
    the file-system. This greatly speeds up master mirror scanning
    and reduces overall I/O on the storage system.
    If no 'fullfiletimelist-*' file is found the functions returns
    False and umdl can fall back to disk based master mirror scanning.

    :param session: SQLAlchemy session
    :param config: umdl config
    :param diskpath: top directory of the category where the
                     master mirror scanning starts
    :param category: SQLAlchemy object of a MirrorManager category
    :returns: True for success; False for failure
    """

    def _handle_fedora_linux_category(path):
        if category.name == "Fedora Linux":
            # The 'Fedora Linux' category is the only category
            # which starts at one directory level lower.
            # 'Fedora Linux' -> pub/fedora/linux
            # 'Fedora EPEL' -> pub/epel
            # fullfiletimelist-fedora starts at linux/
            # need to remove 'linux/' so that topdir + filename
            # point to the right file
            return path[6:]
        return path

    # let's look for a fullfiletimelist-* file
    try:
        if category.name == "Fedora Linux":
            filelist = glob.glob("%s/../fullfiletimelist-*" % diskpath)
        else:
            filelist = glob.glob("%s/fullfiletimelist-*" % diskpath)
    except Exception:
        return False

    if len(filelist) < 1:
        # not a single element found in the glob
        return False

    # blindly take the first file found by the glob
    logger.info("Loading and parsing %s" % filelist[0])
    # A hash with directories as key and ctime as value
    ctimes = {}
    # A hash with directories as key and
    # { filename: { 'stat' : ctime, 'size': 'filesize' } } as value
    files = {}
    seen = set()
    # A set with a list of directories with a repository (repodata)
    repo = set()

    umdl_prefix = config["UMDL_PREFIX"]
    # Not opening the file as stream and reading line by line as this breaks
    # if the file changes. As this can happen, the file is loaded once into
    # memory using mmap.
    with open(filelist[0], "rb") as f:
        # tell mmap to open file read-only or mmap might fail
        m = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        row = m.readline()
        while row:
            col = row.split()
            row = m.readline()
            # only rows with at least 4 columns are what we are looking for
            # 'ctime\ttype\tsize\tname'
            if len(col) >= 4:
                # Type can be either 'f', 'd', 'f-', 'd-'.
                # As long as the '-' support is not implemented only look
                # for the first character so that this does not break
                # once types with '-' can appear.
                # https://pagure.io/quick-fedora-mirror/issue/40

                # only files (type: f)
                if col[1][0] == "f":
                    # put all the information in a dict with path as key
                    tmp = os.path.dirname(_handle_fedora_linux_category(col[3]))
                    tmp = os.path.join(diskpath, tmp).replace(umdl_prefix, "")
                    tmp = str(tmp, "utf8")

                    tmp2 = os.path.basename(_handle_fedora_linux_category(col[3]))
                    tmp2 = str(tmp2, "utf8")

                    if tmp in seen:
                        files[tmp].update({tmp2: {"stat": int(col[0]), "size": col[2]}})
                    else:
                        files[tmp] = {tmp2: {"stat": int(col[0]), "size": col[2]}}
                        # Use a set() to track if the element already exists in the dict().
                        # This is much faster than if tmp in files.keys(); much much faster
                        seen.add(tmp)
                elif col[1][0] == "d":
                    # get all directories and their ctime
                    tmp = os.path.join(diskpath, _handle_fedora_linux_category(col[3]))

                    tmp = tmp.replace(umdl_prefix, "")
                    tmp = str(tmp, "utf8")
                    ctimes[tmp] = int(col[0])
                    # Only if a directory contains a 'repodata' directory
                    # it should be used for repository creation.
                    if "repodata" in tmp:
                        # There is a 'repodata' directory, add the parent
                        # directory to the repo set().
                        # Remove '/repodata'
                        repo.add(tmp[:-9])

    # add the root directory of the current category
    tmp = str(diskpath.replace(umdl_prefix, ""), "utf8")
    ctimes[tmp] = 0

    logger.debug("sync_directories_from_fullfiletimelist %r" % diskpath)
    seen = set()

    for dirname in ctimes.keys():
        if dirname in seen:
            logger.info("Skipping already seen directory %s" % (dirname))
            continue
        seen.add(dirname)
        if is_excluded(dirname, stdexcludes):
            logger.info("Excluding %s" % (dirname))
            continue
        try:
            file_dict = files[dirname]
        except Exception:
            # An empty directory is not part of files{}
            file_dict = {}

        if dirname in repo:
            is_repo = True
        else:
            is_repo = False

        sync_category_directory(
            session, config, category, dirname, ctimes[dirname], file_dict, is_repo
        )

    if category.delete_directories:
        nuke_gone_directories(session, None, category, ctimes)

    return True


def setup_logging(config, debug, logfile, list_categories):
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

    fmt = "%(asctime)s:%(category)s:%(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    handler = logging.handlers.WatchedFileHandler(log_file, "a+")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    f = MasterFilter()
    logger.addFilter(f)
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
    "--skip-fullfiletimelist",
    is_flag=True,
    default=False,
    help="Do not look for a fullfiletimelist-*; actually scan the filesystem",
)
@click.option(
    "--delete-directories",
    is_flag=True,
    default=False,
    help="delete directories from the database that are no longer " "on disk",
)
def main(
    config, logfile, list_categories, categories, debug, skip_fullfiletimelist, delete_directories
):
    global cname

    config = read_config(config)
    db_manager = get_db_manager(config)
    session = db_manager.Session()

    setup_logging(config, debug, logfile, list_categories)

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
        category.delete_directories = delete_directories

        if i["type"] == "rsync":
            sync_directories_using_rsync(session, config, i["url"], category)

        if i["type"] == "file":
            sync_directories_from_file(session, config, i["url"], category)
        if i["type"] == "directory":
            found = False
            if not skip_fullfiletimelist:
                found = sync_directories_from_fullfiletimelist(session, config, i["path"], category)

            if skip_fullfiletimelist or not found:
                sync_directories_from_disk(session, config, i["path"], category)

    logger.info("Refresh the list of repomd.xml")
    Directory.age_file_details(session, config)

    session.commit()

    logger.info("Ending umdl")
