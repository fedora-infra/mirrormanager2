#!/usr/bin/env python

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

import glob
import logging
import re
import optparse
import os
import stat
import sys
import yum.repoMDObject
import datetime
import time
import hashlib


sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))
import mirrormanager2.lib
from mirrormanager2.lib.model import (
    Arch, Directory, Repository, Version, FileDetail)
from mirrormanager2.lib.repomap import repo_prefix
from mirrormanager2.lib.sync import run_rsync


delete_directories=False
logger = logging.getLogger('umdl')
stdexcludes=['.*\.snapshot', '.*/\.~tmp~']
PREFIX = '/srv/'


def parent_dir(path):
    sdir = path.split('/')[:-1]
    try:
        parent = os.path.join(*sdir)
    except TypeError: #
        parent = u''
    return parent


def remove_category_topdir(topdirName, path):
    path = path[len(topdirName)+1:]
    return path


def _get_version_from_path(path):
    # Debian/Ubuntu versioning
    # this ignores 10.10 and maverick-{anything}, but picks up 'maverick'
    s = r'dists/(\w+)/'
    m = re.search(re.compile(s), path)
    if m is not None:
        return m.group(1)
    # Fedora versioning
    s = r'/?(([\.\d]+)([-_]\w+)?)/'
    m = re.search(re.compile(s), path)
    if m is not None:
        return m.group(1)
    # Rawhide, development
    if 'rawhide' in path:
        return 'development'
    return None


def create_version_from_path(session, category, path):
    ver = None
    vname = _get_version_from_path(path)
    if vname is not None and vname != '':
        test_paths = [ u'/test/', u'/stage/']
        if any(x in path for x in test_paths):
            isTest = True
        else:
            isTest = False

        ver = mirrormanager2.lib.get_version_by_name_version(
            session, category.product.name, vname)
        if not ver:
            logger.info(
                'Created Version(product=%s, name=%s, is_test=%s, '
                % (category.product, vname, isTest))
            ver = Version(
                product=category.product,
                name=vname,
                is_test=isTest)
            session.add(ver)
            session.flush()

    return ver

arch_cache = None
version_cache = None


def setup_arch_version_cache(session):
    global arch_cache
    if arch_cache is None:
        arch_cache = mirrormanager2.lib.get_arches(session)

    global version_cache
    if version_cache is None:
        version_cache = mirrormanager2.lib.get_versions(session)


def guess_ver_arch_from_path(session, category, path):
    arch = None
    if 'SRPMS' in path:
        arch = mirrormanager2.lib.get_arch_by_name(session, 'source')
    else:
        for a in arch_cache:
            s = '.*(^|/)%s(/|$).*' % (a['name'])
            if re.compile(s).match(path):
                arch = mirrormanager2.lib.get_arch_by_name(session, a['name'])
                break

    ver = None
    # newest versions/IDs first, also handles stupid Fedora 9.newkey hack.
    for v in version_cache:
        if v['product_id'] != category.product.id:
            continue
        s = '.*(^|/)%s(/|$).*' % (v['name'])
        if re.compile(s).match(path):
            ver = mirrormanager2.lib.get_version_by_id(session, v['id'])
            break

    # create Versions if we can figure it out...
    if ver is None:
        ver = create_version_from_path(session, category, path)
        if ver:
            version_cache.append(ver)
    return (ver, arch)


# Something like this is committed to yum upstream, but may not be in the
# copy we are using.
def set_repomd_timestamp(yumrepo):
    timestamp = 0
    for ft in yumrepo.fileTypes():
        thisdata = yumrepo.repoData[ft]
        timestamp = max(int(thisdata.timestamp), timestamp)
    yumrepo.timestamp = timestamp
    return timestamp


def make_repo_file_details(session, config, relativeDName, D, category, target):

    warning = "Won't make repo file details"

    # For yum repos and ostree repos
    allowed_targets = ['repomd.xml', 'summary']
    if target not in allowed_targets:
        logger.warning("%s: %r not in %r" % (warning, target, allowed_targets))
        return

    absolutepath = os.path.join(
        config.get('UMDL_PREFIX', ''), category.topdir.name,
        relativeDName, target)

    if not os.path.exists(absolutepath):
        logger.warning("%s: %r does not exist" % (warning, absolutepath))
        return

    try:
        f = open(absolutepath, 'r')
        contents = f.read()
        f.close()
    except:
        return

    size = len(contents)
    md5 = hashlib.md5(contents).hexdigest()
    sha1 = hashlib.sha1(contents).hexdigest()
    sha256 = hashlib.sha256(contents).hexdigest()
    sha512 = hashlib.sha512(contents).hexdigest()

    if target == 'repomd.xml':
        yumrepo = yum.repoMDObject.RepoMD('repoid', absolutepath)
        if 'timestamp' not in yumrepo.__dict__:
            set_repomd_timestamp(yumrepo)
        timestamp = yumrepo.timestamp
    elif target == 'summary':
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
        timestamp=timestamp)
    if not fd:
        fd = FileDetail(
            directory_id=D.id,
            filename=target,
            sha1=sha1,
            md5=md5,
            sha256=sha256,
            sha512=sha512,
            timestamp=timestamp,
            size=size)
        session.add(fd)
        session.flush()


def make_repository(session, directory, relativeDName, category, target):

    logger.info(
        "Checking into Repo %s - %s - cat: %s - target: %s"
        % (directory, relativeDName, category, target))

    warning = "Won't make repository object"

    # For yum repos and ostree repos
    allowed_targets = ['repomd.xml', 'summary']
    if target not in allowed_targets:
        logger.warning("%s: %r not in %r" % (warning, target, allowed_targets))
        return

    if target == 'repomd.xml':
        (ver, arch) = guess_ver_arch_from_path(
            session, category, relativeDName)
        if ver is None or arch is None:
            logger.warning("%s: could not guess version and arch %r, %r" % (
                warning, ver, arch))
            return None
    elif target == 'summary':
        # For ostree, we someday need to actually extract the arch information
        # from the ostree repo, but for now (F21 and F22) we will only be
        # shipping x86_64, so we hardcode that.  At present, it is not possible
        # to query an ostree repo for the arch information.  Bug walters about
        # this.
        arch = mirrormanager2.lib.get_arch_by_name(session, 'x86_64')
        # Furthermore, we'll grab the version piece from the path which looks
        # like atomic/rawhide or atomic/21.
        ver = relativeDName.rstrip('/').split('/')[-1]
        ver = mirrormanager2.lib.get_version_by_name_version(
            session, category.product.name, ver)
        if ver is None:
            if not relativeDName.endswith('/'):
                relativeDName += '/'
            ver = create_version_from_path(category, relativeDName)
            session.add(ver)
            session.flush()
            version_cache.append(ver)

    # stop making duplicate Repository objects.
    if len(directory.repositories) > 0:
        logger.warning("%s: directory already has a repository")
        return None

    repo = None
    prefix = repo_prefix(relativeDName, category, ver)
    repo = mirrormanager2.lib.get_repo_prefix_arch(
        session, prefix, arch.name)
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
            prefix=prefix)
        logger.info(
            'Created Repository(prefix=%s, version=%s, arch=%s, '
            'category=%s) -> Directory %s'
            % (prefix, ver.name, arch.name, category.name, directory.name))
        session.add(repo)
        session.flush()
    else:
        logger.info(
            'Adjusting prefix Repository(%s) %s -> %s'
            % (repo, repo.prefix, prefix))
        if repo.prefix != prefix:
            repo.prefix = prefix

    return repo


def short_filelist(config, relativeDName, files):
    html=0
    rpms=0
    hdrs=0
    drpms=0
    for f in files:
        if f.endswith('.html'):  html += 1
        if f.endswith('.rpm'):   rpms += 1
        if f.endswith('.hdr'):   hdrs += 1
        if f.endswith('.drpm'): drpms += 1
    if html>10 or rpms > 10 or hdrs > 10 or drpms > 10:
        date_file_list = []
        rc = {}
        for k in files:
            try:
                s = os.stat(os.path.join(
                    config.get('UMDL_PREFIX', ''), relativeDName, k))
            except OSError:
                continue

            date_file_tuple = (s[stat.ST_CTIME], k, str(s.st_size))
            date_file_list.append(date_file_tuple)
        date_file_list.sort()
        # keep the most recent 3
        date_file_list = date_file_list[-3:]

        return [item[1] for item in date_file_list]
    else:
        return files


def sync_category_directory(
        session, config, category, relativeDName, readable, ctime):

    logger.debug("  sync_category_directory %s - %s" % (
        category, relativeDName))

    created = False
    relativeDName = relativeDName.replace(category.topdir.name, '')
    if relativeDName.startswith('/'):
        relativeDName = relativeDName[1:]
    if relativeDName in category.directory_cache:
        d = category.directory_cache[relativeDName]
        if d['readable'] != readable:
            set_readable = True
        if d['ctime'] != ctime:
            set_ctime = True
        D = mirrormanager2.lib.get_directory_by_id(session, d.id)
    else:
        if relativeDName == u'':
            D = category.topdir
        else:
            # Can't find the new directory, just add it
            dname = os.path.join(category.topdir.name, relativeDName)
            D = Directory(name=dname, readable=readable, ctime=ctime)
            logger.debug(
                u'Created Directory(%s, readable=%s, ctime=%s)'
                % (dname, readable, ctime))
            created = True
        # Add this category to the directory
        D.categories.append(category)
        session.add(D)
        # And flush so that we can already start using it
        session.flush()
        # Refresh the cache
        category.directory_cache[relativeDName] = D


    D.readable = readable
    dirfiles = os.listdir(os.path.join(
        PREFIX, category.topdir.name, relativeDName))
    if D.ctime != ctime or created:
        shortfiles = short_filelist(config, relativeDName, dirfiles)
        if D.files != shortfiles:
            D.files = shortfiles
    session.add(D)
    session.flush()

    if 'repodata' in dirfiles:
        make_repository(session, D, relativeDName, category, 'repomd.xml')
        make_repo_file_details(
            session, config, relativeDName, D, category, 'repomd.xml')
    elif 'summary' in dirfiles:
        make_repository(session, D, relativeDName, category, 'summary')
        make_repo_file_details(
            session, config, relativeDName, D, category, 'summary')
