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
summary file), it will create a repository object (cf `Repomaker`) which
is basically a mapping between a yum repo name (ie: Fedora-20-updates) and a
directory (/pub/fedora/linux/updates/....)

"""

import hashlib
import logging
import os
import re
import stat
from itertools import chain

import rpmmd.repoMDObject

import mirrormanager2.lib
from mirrormanager2.lib.model import FileDetail, Repository, Version
from mirrormanager2.lib.repomap import repo_prefix

logger = logging.getLogger(__name__)


# For ostree, we someday need to actually extract the arch information
# from the ostree repo, but for now (F21 and F22) we will only be
# shipping x86_64, so we hardcode that.  At present, it is not possible
# to query an ostree repo for the arch information.  Bug walters about
# this.
OSTREE_ARCH = "x86_64"


def parent_dir(path):
    sdir = path.split("/")[:-1]
    try:
        return os.path.join(*sdir)
    except TypeError:
        return ""


def _get_version_from_path(path):
    # Debian/Ubuntu versioning
    # this ignores 10.10 and maverick-{anything}, but picks up 'maverick'
    s = r"dists/(\w+)/"
    m = re.search(re.compile(s), path)
    if m is not None:
        return m.group(1)
    # Fedora versioning
    s = r"/(([\.\d]+)([-_]\w+)?)/"
    m = re.search(re.compile(s), path)
    if m is not None:
        return m.group(1)
    # Rawhide, development
    if "rawhide" in path:
        return "development"
    return None


# Something like this is committed to yum upstream, but may not be in the
# copy we are using.
def set_repomd_timestamp(yumrepo):
    timestamp = 0
    for ft in yumrepo.fileTypes():
        thisdata = yumrepo.repoData[ft]
        timestamp = max(int(thisdata.timestamp), timestamp)
    yumrepo.timestamp = timestamp
    return timestamp


class FileDetailFromChecksumsLoader:
    sha1_globs = list(re.compile(p) for p in [r".*\.sha1sum", "SHA1SUM", "sha1sum.txt"])
    md5_globs = list(re.compile(p) for p in [r".*\.md5sum", "MD5SUM", "md5sum.txt"])
    sha256_globs = list(re.compile(p) for p in [".*-CHECKSUM", "sha256sum.txt"])
    sha512_globs = list(re.compile(p) for p in [r".*\.sha512sum", "SHA512SUM", "sha512sum.txt"])

    def __init__(self, session, config, directory, relative_dir_name=None):
        """
        :param session: SQLAlchemy session
        :param config: umdl config
        :param directory: MirrorManager database directory object
        """
        self.session = session
        self.config = config
        self.directory = directory
        self.relative_dir_name = relative_dir_name or self.directory.name

    def _handle_checksum_line(self, line, checksumlen):
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

    def _parse_checksum_file(self, relativeDName, checksumlen):
        r = {}
        try:
            with open(os.path.join(self.config["UMDL_PREFIX"], relativeDName)) as f:
                for line in f:
                    filename, checksum = self._handle_checksum_line(line, checksumlen)
                    if filename is not None:
                        r[filename] = checksum
        except Exception:
            pass
        return r

    def _checksums_from_globs(self, globs, checksumlen):
        """
        Finds checksum files on disk (or from the filelist) and extracts
        the checksums and places the result in a dict[filename] = checksum.
        Finding the checksum files does a os.listdir() if the variable
        files is None.

        :param globs: possible patterns containing checksums
        :param checksumlen: number of characters the checksum has
        :returns: dict[filename] = checksum
        """

        d = {}
        checksum_files = []
        for g in globs:
            for f in self._get_filenames():
                if g.match(f):
                    checksum_files.append(os.path.join(self.relative_dir_name, f))
        for f in checksum_files:
            d.update(self._parse_checksum_file(f, checksumlen))
        return d

    def _get_filenames(self):
        yield from os.listdir(os.path.join(self.config["UMDL_PREFIX"], self.relative_dir_name))

    def _get_size_and_ctime(self, f):
        try:
            s = os.stat(os.path.join(self.config["UMDL_PREFIX"], self.relative_dir_name, f))
        except OSError:
            # bail if the file doesn't actually exist
            return None, None
        return s.st_size, s[stat.ST_CTIME]

    def load(self):
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
        :param directory: MirrorManager database directory object
        :param files: optional hash with the files in the directory; if this is
                    None, the function will actually scan the directory :directory:
        """
        md5dict = self._checksums_from_globs(self.md5_globs, 32)
        sha1dict = self._checksums_from_globs(self.sha1_globs, 40)
        sha256dict = self._checksums_from_globs(self.sha256_globs, 64)
        sha512dict = self._checksums_from_globs(self.sha512_globs, 128)

        sum_files = set(chain(md5dict, sha1dict, sha256dict, sha512dict))

        for f in sum_files:
            size, ctime = self._get_size_and_ctime(f)
            if size is None or ctime is None:
                continue
            sha1 = sha1dict.get(f)
            md5 = md5dict.get(f)
            sha256 = sha256dict.get(f)
            sha512 = sha512dict.get(f)

            fd_attrs = dict(
                directory_id=self.directory.id,
                filename=f,
                sha1=sha1,
                md5=md5,
                sha256=sha256,
                sha512=sha512,
                timestamp=ctime,
                size=size,
            )

            fd = mirrormanager2.lib.get_file_detail(self.session, **fd_attrs)
            if not fd:
                fd = FileDetail(**fd_attrs)
                self.session.add(fd)
                self.session.commit()
                logger.debug("Added checksum for %s to database", f)


class FileDetailFromChecksumsListLoader(FileDetailFromChecksumsLoader):
    def __init__(self, session, config, directory, files, relative_dir_name=None):
        super().__init__(session, config, directory, relative_dir_name)
        self.files = files

    def _get_filenames(self):
        yield from self.files.keys()

    def _get_size_and_ctime(self, f):
        try:
            size = int(self.files[f]["size"])
            ctime = self.files[f]["stat"]
        except KeyError:
            # there are seldom cases where the CHECKSUM file
            # points to files in a sub-directory like
            # pxeboot/vmlinuz; ignore it for now
            return None, None
        return size, ctime


class RepoMaker:
    allowed_targets = ["repomd.xml", "summary"]

    def __init__(self, session, config):
        self.session = session
        self.config = config
        self._arch_cache = None
        self._version_cache = None

    @property
    def arch_cache(self):
        if self._arch_cache is None:
            self._arch_cache = mirrormanager2.lib.get_arches(self.session)
        return self._arch_cache

    @property
    def version_cache(self):
        if self._version_cache is None:
            self._version_cache = mirrormanager2.lib.get_versions(self.session)
        return self._version_cache

    def create_version_from_path(self, category, path):
        ver = None
        vname = _get_version_from_path(path)
        if vname is not None and vname != "":
            test_paths = ["/test/", "/stage/"]
            if any(x in path for x in test_paths):
                isTest = True
            else:
                isTest = False

            ver = mirrormanager2.lib.get_version_by_name_version(
                self.session, category.product.name, vname
            )
            if not ver:
                logger.info(
                    f"Created Version(product={category.product}, name={vname}, is_test={isTest}, "
                )
                ver = Version(product=category.product, name=vname, is_test=isTest)
                self.session.add(ver)
                self.session.flush()

        return ver

    def guess_ver_arch_from_path(self, category, path):
        arch = None
        if "SRPMS" in path:
            arch = mirrormanager2.lib.get_arch_by_name(self.session, "source")
        else:
            for a in self.arch_cache:
                s = f".*(^|/){a.name}(/|$).*"
                if re.compile(s).match(path):
                    arch = mirrormanager2.lib.get_arch_by_name(self.session, a.name)
                    break

        ver = None
        # newest versions/IDs first, also handles stupid Fedora 9.newkey hack.
        for v in self.version_cache:
            if v.product_id != category.product.id:
                continue
            s = f".*(^|/){v.name}(/|$).*"
            if re.compile(s).match(path):
                ver = mirrormanager2.lib.get_version_by_id(self.session, v.id)
                break

        # create Versions if we can figure it out...
        if ver is None:
            ver = self.create_version_from_path(category, path)
            if ver:
                self.version_cache.append(ver)
        return (ver, arch)

    def make_repo(self, directory, relativeDName, category, target):
        logger.debug(
            f"Checking into Repo {directory} - {relativeDName} - cat: {category} - target: {target}"
        )

        # stop making duplicate Repository objects.
        if len(directory.repositories) > 0:
            logger.debug("%s: directory already has a repository", directory.name)
            return None

        warning = "Won't make repository object"

        # For yum repos and ostree repos

        if target not in self.allowed_targets:
            logger.warning(f"{warning}: {target!r} not in {self.allowed_targets!r}")
            return

        if target == "repomd.xml":
            dname = os.path.join(category.topdir.name, relativeDName)
            for skip in self.config["SKIP_PATHS_FOR_VERSION"]:
                if dname.startswith(skip):
                    logger.debug("Skipping path %s as requested by SKIP_PATHS_FOR_VERSION", dname)
                    return None
            ver, arch = self.guess_ver_arch_from_path(category, relativeDName)
            if ver is None or arch is None:
                logger.warning(f"{warning}: could not guess version and arch {ver!r}, {arch!r}")
                return None
        elif target == "summary":
            arch = mirrormanager2.lib.get_arch_by_name(self.session, OSTREE_ARCH)
            # Furthermore, we'll grab the version piece from the path which looks
            # like atomic/rawhide or atomic/21.
            ver = relativeDName.rstrip("/").split("/")[-1]
            ver = mirrormanager2.lib.get_version_by_name_version(
                self.session, category.product.name, ver
            )
            if ver is None:
                if not relativeDName.endswith("/"):
                    relativeDName += "/"
                ver = self.create_version_from_path(category, relativeDName)
                self.session.add(ver)
                self.session.flush()
                self.version_cache.append(ver)

        repo = None
        prefix = repo_prefix(relativeDName, category, ver)
        repo = mirrormanager2.lib.get_repo_prefix_arch(self.session, prefix, arch.name)
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
            self.session.add(repo)
            self.session.flush()
        else:
            if repo.prefix != prefix:
                repo.prefix = prefix
                logger.info(f"Adjusting prefix Repository({repo}) {repo.prefix} -> {prefix}")

        return repo

    def make_file_details(self, D, diskpath, relativeDName, target):
        warning = "Won't make repo file details"

        if diskpath is None:
            logger.warning("%s: diskpath is None", warning)
            return

        # For yum repos and ostree repos
        if target not in self.allowed_targets:
            logger.warning(f"{warning}: {target!r} not in {self.allowed_targets!r}")
            return

        absolutepath = os.path.join(diskpath, relativeDName, target)

        if not os.path.exists(absolutepath):
            logger.warning(f"{warning}: {absolutepath!r} does not exist")
            return

        try:
            with open(absolutepath, "rb") as f:
                contents = f.read()
        except Exception:
            logger.exception("Error reading %s", absolutepath)
            return

        size = len(contents)
        md5 = hashlib.md5(contents).hexdigest()
        sha1 = hashlib.sha1(contents).hexdigest()
        sha256 = hashlib.sha256(contents).hexdigest()
        sha512 = hashlib.sha512(contents).hexdigest()

        if target == "repomd.xml":
            yumrepo = rpmmd.repoMDObject.RepoMD("repoid", absolutepath)
            if "timestamp" not in yumrepo.__dict__:
                set_repomd_timestamp(yumrepo)
            timestamp = yumrepo.timestamp
        elif target == "summary":
            # TODO -- ostree repos may have a timestamp in their summary file
            # someday.  for now, just use the system mtime.
            timestamp = os.path.getmtime(absolutepath)

        fd_attrs = dict(
            directory_id=D.id,
            filename=target,
            sha1=sha1,
            md5=md5,
            sha256=sha256,
            sha512=sha512,
            size=size,
            timestamp=timestamp,
        )
        fd = mirrormanager2.lib.get_file_detail(
            self.session,
            **fd_attrs,
        )
        if not fd:
            fd = FileDetail(
                **fd_attrs,
            )
            self.session.add(fd)
            self.session.flush()
            created = True
        else:
            created = False
        logger.debug(f"Updating FileDetail {fd.id} for {absolutepath!r}")
        return created
