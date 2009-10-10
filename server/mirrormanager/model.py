from sqlobject import *
from sqlobject.sqlbuilder import *
from turbogears import identity, config
import pickle
import sys
from datetime import datetime
import time
from string import rstrip, strip
import re
import IPy
from mirrormanager.lib import uniqueify
from mirrormanager.categorymap import categorymap
IPy.check_addr_prefixlen = 0

from turbogears.database import PackageHub


hub = PackageHub("mirrormanager")
__connection__ = hub

class SiteToSite(SQLObject):
    class sqlmeta:
        cacheValues = False
    upstream_site = ForeignKey('Site')
    downstream_site = ForeignKey('Site')
    idx = DatabaseIndex('upstream_site', 'downstream_site', unique=True)

    def my_site(self):
        return self.upstream_site

class Site(SQLObject):
    class sqlmeta:
        cacheValues = False
    name = UnicodeCol(alternateID=True, length=32)
    password = UnicodeCol(default=None, length=32)
    orgUrl = UnicodeCol(default=None, length=255)
    private = BoolCol(default=False)
    admin_active = BoolCol(default=True)
    user_active  = BoolCol(default=True)
    createdAt = DateTimeCol(default=datetime.utcnow())
    createdBy = UnicodeCol(default=None, length=32)
    # allow all sites to pull from me
    allSitesCanPullFromMe = BoolCol(default=False)
    downstreamComments = StringCol(default=None)
    
    admins = MultipleJoin('SiteAdmin')
    hosts  = MultipleJoin('Host')

    def destroySelf(self):
        """Cascade the delete operation"""
        for h in self.hosts:
            h.destroySelf()
        for a in self.admins:
            a.destroySelf()
        for s in SiteToSite.select(OR(SiteToSite.q.upstream_siteID == self.id,
                                        SiteToSite.q.downstream_siteID == self.id)):
            s.destroySelf()
        SQLObject.destroySelf(self)

    def _get_downstream_sites(self):
        if self.allSitesCanPullFromMe:
            return [s for s in Site.select() if s != self]
        else:
            return [s2s.downstream_site for s2s in SiteToSite.selectBy(upstream_site=self)]

    def _get_upstream_sites(self):
        open_upstreams   = [s for s in Site.select() if s != self and s.allSitesCanPullFromMe]
        chosen_upstreams = [s2s.upstream_site for s2s in SiteToSite.selectBy(downstream_site=self)]
        result = uniqueify(open_upstreams + chosen_upstreams)
        return result

    def add_downstream_site(self, site):
        if site is not None:
            SiteToSite(upstream_site=self, downstream_site=site)

    def del_downstream_site(self, site):
        for s in SiteToSite.selectBy(upstream_site=self, downstream_site=site):
            s.destroySelf()
        
    def is_siteadmin_byname(self, name):
        for a in self.admins:
            if a.username == name:
                return True
        return False

    def is_siteadmin(self, identity):
        admin_group = config.get('mirrormanager.admin_group', 'sysadmin')
        if identity.in_group(admin_group):
            return True
        return self.is_siteadmin_byname(identity.current.user_name)

    
    def is_downstream_siteadmin_byname(self, name):
        for d in self.downstream_sites:
            for a in d.admins:
                if a.username == name:
                    return True
        return False

    def is_downstream_siteadmin(self, identity):
        """If you are a sysadmin of one of my immediate downstream sites,
        you can see some of my site details, but you can't edit them.
        """
        return self.is_downstream_siteadmin_byname(identity.current.user_name)
        

class SiteAdmin(SQLObject):
    class sqlmeta:
        cacheValues = False
    username = UnicodeCol(length=32)
    site = ForeignKey('Site')

    def my_site(self):
        return self.site

def user_sites(identity):
    return Site.select(join=INNERJOINOn(Site, SiteAdmin, AND(SiteAdmin.q.siteID == Site.q.id,
                                                             SiteAdmin.q.username == identity.current.user_name)))


class HostCategory(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    category = ForeignKey('Category')
    hcindex = DatabaseIndex('host', 'category', unique=True)
    admin_active = BoolCol(default=True)
    user_active = BoolCol(default=True)
    upstream = UnicodeCol(default=None, length=255)
    always_up2date = BoolCol(default=False)
    dirs = MultipleJoin('HostCategoryDir', orderBy='path')
    urls = MultipleJoin('HostCategoryUrl')

    def destroySelf(self):
        """Cascade the delete operation"""
        for b in self.urls:
            b.destroySelf()
        for d in self.dirs:
            d.destroySelf()
        SQLObject.destroySelf(self)

    def my_site(self):
        return self.host.my_site()


class HostCategoryDir(SQLObject):
    class sqlmeta:
        cacheValues = False
    host_category = ForeignKey('HostCategory')
    # subset of the path starting below HostCategory.path
    path = UnicodeCol(length=255)
    directory = ForeignKey('Directory')
    hcdindex = DatabaseIndex('host_category', 'path', unique=True)
    up2date = BoolCol(default=True)
    files = PickleCol(default=None)
    lastCrawled = DateTimeCol(default=None)
    

class HostCategoryUrl(SQLObject):
    class sqlmeta:
        cacheValues = False
    host_category = ForeignKey('HostCategory')
    url = UnicodeCol(alternateID=True, length=255)
    private = BoolCol(default=False)

    def my_site(self):
        return self.host_category.my_site()
    
class Host(SQLObject):
    class sqlmeta:
        cacheValues = False
    name = UnicodeCol(length=255)
    site = ForeignKey('Site')
    idx = DatabaseIndex('site', 'name', unique=True)
    robot_email = UnicodeCol(default=None, length=255)
    admin_active = BoolCol(default=True)
    user_active = BoolCol(default=True)
    country = StringCol(default=None)
    bandwidth = UnicodeCol(default=None, length=255)
    bandwidth_int = IntCol(default=100)
    comment = StringCol(default=None)
    _config = PickleCol(default=None)
    lastCheckedIn = DateTimeCol(default=None)
    lastCrawled = DateTimeCol(default=None)
    private = BoolCol(default=False)
    internet2 = BoolCol(default=False)
    internet2_clients = BoolCol(default=False)
    asn = IntCol(default=None)
    asn_clients = BoolCol(default=True)
    countries_allowed = MultipleJoin('HostCountryAllowed')
    netblocks = MultipleJoin('HostNetblock', orderBy='netblock')
    acl_ips = MultipleJoin('HostAclIp', orderBy='ip')
    categories = MultipleJoin('HostCategory')
    exclusive_dirs = MultipleJoin('DirectoryExclusiveHost')

    def destroySelf(self):
        """Cascade the delete operation"""
        s = [self.countries_allowed,
             self.netblocks,
             self.acl_ips,
             self.categories]
        for a in s:
            for b in a:
                b.destroySelf()
        for ed in self.exclusive_dirs:
            ed.destroySelf()
        SQLObject.destroySelf(self)



    def _uploaded_config(self, config):
        message = ''

        def _config_categories(config):
            noncategories = ['version', 'global', 'site', 'host', 'stats']
            if config is not None:
                return [key for key in config.keys() if key not in noncategories]
            else:
                return []

        def compare_dir(hcdir, files):
            if hcdir.directory is None or hcdir.directory.files is None:
                raise SQLObjectNotFound
            dfiles = hcdir.directory.files
            if len(dfiles) == 0 and len(files) == 0:
                return True
            for fname, fdata in dfiles.iteritems():
                if fname not in files:
                    return False
                if fdata['size'] != files[fname]:
                    return False
            return True


        # handle the optional arguments
        if config['host'].has_key('user_active'):
            self.user_active = config['host']['user_active']

        # fill in the host category data (HostCategory and HostCategoryURL)
        # the category names in the config have been lowercased
        # so we have to find the matching mixed-case category name.
        cats = {}
        for c in Category.select():
            cats[c.name.lower()] = c.id

        for c in _config_categories(config):
            if c not in cats:
                continue
            category = Category.get(cats[c])
            hc = HostCategory.selectBy(host=self, category=category)
            if hc.count() > 0:            
                hc = hc[0]
            else:
                hc = HostCategory(host=self, category=category)

            marked_up2date = 0
            deleted = 0
            added = 0
            # and now one HostCategoryDir for each dir in the dirtree
            if config[c].has_key('dirtree'):
                for dirname,files in config[c]['dirtree'].iteritems():
                    d = strip(dirname, '/')
                    hcdir = HostCategoryDir.selectBy(host_category = hc, path=d)
                    if hcdir.count() > 0:
                        hcdir = hcdir[0]
                        # this is evil, but it avoids stat()s on the client side and a lot of data uploading
                        is_up2date = True
                        marked_up2date += 1
                        if hcdir.up2date != is_up2date:
                            hcdir.up2date = is_up2date
                            hcdir.sync()
                    else:
                        if len(d) > 0:
                            dname = "%s/%s" % (hc.category.topdir.name, d)
                        else:
                            dname = hc.category.topdir.name

                        # Don't create an entry for a directory the database doesn't know about
                        try:
                            dir = Directory.byName(dname)
                            hcdir = HostCategoryDir(host_category=hc, path=d, directory=dir)
                            added += 1
                        except:
                            pass
                for d in HostCategoryDir.selectBy(host_category=hc):
                    if d.path not in config[c]['dirtree'].keys():
                        d.destroySelf()
                        deleted += 1

                message += "Category %s directories updated: %s  added: %s  deleted %s\n" % (category.name, marked_up2date, added, deleted)
            hc.sync()

        return message


    def is_admin_active(self):
        return self.admin_active and self.site.admin_active

    def is_active(self):
        return self.admin_active and self.user_active and self.site.user_active

    def is_private(self):
        return self.private or self.site.private
    
    def _get_config(self):
        return self._config

    def _set_config(self, config):
        # really, we don't store the config anymore
        self._config = None
        self.lastCheckedIn = datetime.utcnow()

    def checkin(self, config):
        message = self._uploaded_config(config)
        self.config = config
        self.sync()
        return message

    def has_category(self, cname):
        return HostCategory.selectBy(host=self, category=Category.byName(cname)).count() > 0
    
    def has_category_dir(self, category, dir):
        if len(dir)==0:
            return True

        sr = HostCategory.select(join=INNERJOINOn(HostCategory, HostCategoryDir,
                                                  AND(HostCategory.q.hostID == self.id,
                                                      HostCategory.q.categoryID == category.id,
                                                      HostCategory.q.id == HostCategoryDir.q.host_categoryID,
                                                      HostCategoryDir.q.path == dir)),
                                 limit=1)
        return sr.count() > 0

    def category_urls(self, cname):
        for hc in self.categories:
            if hc.category.name == cname:
                return [hcurl.url for hcurl in HostCategoryUrl.selectBy(host_category=hc, private=False)]

    def directory_urls(self, directory, category):
        """Given what we know about the host and the categories it carries
        return the URLs by which we can get at it (whether or not it's actually present can be determined later."""
        result = []
        for hc in self.categories:
            if category != hc.category:
                continue
            dirname = directory.name[(len(category.topdir.name)+1):]
            for hcu in self.category_urls(category.name):
                fullurl = '%s/%s' % (hcu, dirname)
                result.append((fullurl, self.country))
        return result

    def my_site(self):
        return self.site

    def set_not_up2date(self):
        for hc in self.categories:
            for hcd in hc.dirs:
                hcd.up2date=False
                hcd.sync()


class PubliclistHostCategory:
    class sqlmeta:
        cacheValues = False
    def __init__(self, name):
        self.name          = name
        self.http_url      = None
        self.ftp_url       = None
        self.rsync_url     = None


    def numurls(self):
        i=0
        if self.http_url  is not None: i=i+1
        if self.ftp_url   is not None: i=i+1
        if self.rsync_url is not None: i=i+1
        return i

    def add_url(self, url):
        if url.startswith('http:'):
	    self.http_url = url
        elif url.startswith('ftp:'):
	    self.ftp_url = url
        elif url.startswith('rsync:'):
	    self.rsync_url = url

class PubliclistHost:
    class sqlmeta:
        cacheValues = False
    def __init__(self, hostinfo):
        self.id      = hostinfo[0]
        self.country = hostinfo[1]
        self.name    = hostinfo[2]
        self.bandwidth_int = hostinfo[3]
        self.comment = hostinfo[4]
        self.internet2 = hostinfo[5]
        self.site_url     = hostinfo[6]
        self.site_name    = hostinfo[7]
        self.categories   = {}

    def __cmp__(self, other):
        """comparison based on country, so we can sort().
        First sort on country, ascending order.
        Second sort on bandwidth_int, decending order.
        """
        a = self.country
        b = other.country
        if a is None:
            a = 'ZZ'
        if b is None:
            b = 'ZZ'
        rc = cmp(a.upper(), b.upper())
        if rc == 0:
            rc = -cmp(self.bandwidth_int, other.bandwidth_int)
        return rc

    def add_category(self, name, url):
        if name in self.categories:
            c = self.categories[name]
        else:
            c = PubliclistHostCategory(name)
            self.categories[name] = c
        c.add_url(url)

    def trim_categories(self, keepcategories):
        k = self.categories.keys()
        for c in k:
            if c not in keepcategories:
                del self.categories[c]


def _publiclist_sql_to_list(sqlresult, valid_categories):
        hosts = {}
        for info in sqlresult:
            if info[0] not in hosts:
                hosts[info[0]] = PubliclistHost(info)
            hosts[info[0]].add_category(info[8], info[9])

        hkeys = hosts.keys()
        for h in hkeys:
            hosts[h].trim_categories(valid_categories)
            ckeys = hosts[h].categories.keys()
            for c in ckeys:
                if hosts[h].categories[c].numurls() == 0:
                    del hosts[h].categories[c]

            if len(hosts[h].categories) == 0:
                del hosts[h]

        # turn the dict into a list
        l = []
        for k, v in hosts.iteritems():
            l.append(v)
        l.sort()
        return l

def _publiclist_hosts(product=None, re=None):

    sql1_filter = ''
    sql2_filter = ''
    sql_common_select = "SELECT DISTINCT host.id, host.country, host.name, host.bandwidth_int, host.comment, host.internet2, site.org_url, site.name, category.name, host_category_url.url "
    sql1_from = "FROM category, host_category, host, site, host_category_url, host_category_dir "
    sql2_from = "FROM category, host_category, host, site, host_category_url, directory, category_directory "
    # join conditions
    sql_common  = "WHERE "
    sql_common += "host_category.category_id = category.id AND "
    sql_common += "host_category.host_id = host.id AND "
    sql_common += "host_category_url.host_category_id = host_category.id AND "
    if product is not None:
        sql_common += "category.product_id = %s AND " % product.id
    sql_common += "host.site_id = site.id "
    # select conditions
    # up2date, active, not private
    sql_common += 'AND host.user_active AND site.user_active '
    sql_common += 'AND host.admin_active AND site.admin_active '
    sql_common += 'AND NOT host.private '
    sql_common += 'AND NOT site.private '
    sql_common += 'AND NOT host_category_url.private '
    sql_common += 'AND category.publiclist '

    sql1_join   = 'AND host_category_dir.host_category_id = host_category.id '
    sql2_join   = 'AND category_directory.directory_id = directory.id '
    sql2_join  += 'AND category_directory.category_id = category.id '

    if re is not None:
        sql1_filter = "AND host_category_dir.path ~ '%s' " % re
        sql2_filter = "AND directory.name ~ '%s' " % re

    sql1_up2date = 'AND host_category_dir.up2date '
    sql2_up2date = 'AND host_category.always_up2date '

    sql1 = sql_common_select + sql1_from + sql_common + sql1_filter + sql1_join + sql1_up2date
    sql2 = sql_common_select + sql2_from + sql_common + sql2_filter + sql2_join + sql2_up2date

    sql = "SELECT * FROM ( %s UNION %s ) AS subquery" % (sql1, sql2)

    result = Directory._connection.queryAll(sql)
    return result

def publiclist_hosts(productname=None, vername=None, archname=None):
        """ has a category of product, and an hcd that matches version """
        
        product = None
        if productname is not None:
            try:
                product = Product.byName(productname)
            except SQLObjectNotFound:
                return []
        if vername is not None and archname is not None:
            desiredPath = '(^|/)%s/.*%s/' % (vername, archname)
        elif vername is not None:
            desiredPath = '(^|/)%s/' % vername
        else:
            desiredPath = None

        sqlresult = _publiclist_hosts(product=product, re=desiredPath)
        valid_categories = categorymap(productname, vername)
        return _publiclist_sql_to_list(sqlresult, valid_categories)

class HostAclIp(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    ip = UnicodeCol(length=16)

    def my_site(self):
        return self.host.my_site()

def _rsync_acl_list(internet2_only, public_only):
    sql = "SELECT host_acl_ip.ip "
    sql += "FROM host, site, host_acl_ip "
    # join conditions
    sql += "WHERE "
    sql += "host.site_id = site.id AND "
    sql += "host_acl_ip.host_id = host.id "
    # select conditions
    # admin_active
    sql += 'AND host.admin_active AND site.admin_active '
    if internet2_only:
        sql += 'AND host.internet2 '
    if public_only:
        sql += 'AND NOT host.private '
        sql += 'AND NOT site.private '

    result = Directory._connection.queryAll(sql)
    return result

def rsync_acl_list(internet2_only=False,public_only=False):
    result = _rsync_acl_list(internet2_only, public_only)
    return [t[0] for t in result]

class HostCountryAllowed(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    country = StringCol(notNone=True)

    def my_site(self):
        return self.host.my_site()

class HostNetblock(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    netblock = StringCol()

    def my_site(self):
        return self.host.my_site()


class HostStats(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    _timestamp = DateTimeCol(default=datetime.utcnow())
    type = UnicodeCol(default=None, length=32)
    data = PickleCol(default=None)


class Arch(SQLObject):
    class sqlmeta:
        cacheValues = False
    name = UnicodeCol(alternateID=True, length=8)
    publiclist = BoolCol(default=True)
    primaryArch = BoolCol(default=True)

def publiclist_arches():
    def compare(a, b):
        rc = 0
        if a.publiclist and not b.publiclist:
            rc = -1
        elif not a.publiclist and b.publiclist:
            rc = 1
        if a.primaryArch and not b.primaryArch:
            rc = -1
        if not a.primaryArch and b.primaryArch:
            rc = 1
        if not rc:
            rc = cmp(a.name, b.name)
        if a.name == u'source' or b.name == u'source':
            rc = 1
        return rc

    result = [a for a in Arch.selectBy(publiclist=True)]
    result.sort(compare)
    return result

# e.g. 'fedora' and 'epel'
class Product(SQLObject):
    class sqlmeta:
        cacheValues = False
    name = UnicodeCol(alternateID=True, length=32)
    versions = MultipleJoin('Version', orderBy='name')
    categories = MultipleJoin('Category')

    def destroySelf(self):
        for v in self.versions:
            v.destroySelf()
        for c in self.categories:
            c.destroySelf()
        SQLObject.destroySelf(self)
        

class Version(SQLObject):
    class sqlmeta:
        cacheValues = False
    name = UnicodeCol(length=32)
    product = ForeignKey('Product')
    isTest = BoolCol(default=False)
    display = BoolCol(default=True)
    display_name = UnicodeCol(default=None, length=255)
    ordered_mirrorlist = BoolCol(default=True)


class Directory(SQLObject):
    class sqlmeta:
        cacheValues = False
    # Full path
    # e.g. pub/fedora/linux/core/6/i386/os
    # e.g. pub/fedora/linux/extras
    # e.g. pub/epel
    # e.g. pub/fedora/linux
    name = UnicodeCol(alternateID=True, length=255)
    files = PickleCol(default={})
    readable = BoolCol(default=True)
    ctime = BigIntCol(default=0)
    categories = RelatedJoin('Category')
    repository = SingleJoin('Repository') # zero or one repository, set if this dir contains a yum repo
    host_category_dirs = MultipleJoin('HostCategoryDir')
    fileDetails = MultipleJoin('FileDetail', orderBy=['filename', '-timestamp'])
    exclusive_hosts = MultipleJoin('DirectoryExclusiveHost')

    def destroySelf(self):
        for c in self.categories:
            self.removeCategory(c)
        if self.repository is not None:
            self.repository.destroySelf()
        # don't destroy a whole category if only deleting a directory
        for hcd in self.host_category_dirs:
            hcd.destroySelf()
        for fd in self.fileDetails:
            fd.destroySelf()
        for eh in self.exclusive_hosts:
            eh.destroySelf()
        SQLObject.destroySelf(self)

    def age_file_details(self):
        """For each file, keep at least 1 FileDetail entry, removing
        any others that are more than 7 days old."""
        fd = {}
        weekago = int(time.time()) - (60*60*24*7)

        for f in self.fileDetails:
            if f.filename not in fd:
                fd[f.filename] = [f]
            else:
                fd[f.filename].append(f)
            
        for filename, fds in fd.iteritems():
            if len(fds) > 1:
                for f in fds[1:]:
                    if f.timestamp < weekago:
                        f.destroySelf()

class Category(SQLObject):
    class sqlmeta:
        cacheValues = False
    # Top-level mirroring
    # e.g. core, extras, release, epel
    name = UnicodeCol(alternateID=True, length=32)
    product = ForeignKey('Product')
    canonicalhost = UnicodeCol(default='http://download.fedora.redhat.com', length=255)
    topdir = ForeignKey('Directory', default=None)
    publiclist = BoolCol(default=True)
    directories = RelatedJoin('Directory', orderBy='name') # all the directories that are part of this category
    hostCategories = MultipleJoin('HostCategory')

    def destroySelf(self):
        for hc in self.hostCategories:
            hc.destroySelf()
        SQLObject.destroySelf(self)

    def directories_newer_than(self, since):
        result = []
        for d in self.directories:
            if d.ctime > since:
                result.append(d.name)
        return result

def lookupCategory(s):
    s = s.lower()
    for c in Category.select():
        cname = c.name.lower()
        if cname == s:
            return c
    return None

def rsyncFilter(categories_requested, since):
    """
    @categories_requested: a list of category names
    @since: timestamp
    """
    def _rsyncFilter(categorySearch, since):
        sql = ''
        sql += "SELECT directory.name "
        sql += "FROM category, directory, category_directory "
        sql += "WHERE "
        # join conditions
        sql += "category_directory.category_id = category.id AND "
        sql += "category_directory.directory_id = directory.id AND "
        # select conditions
        sql += "category.id IN %s AND " % categorySearch
        sql += "directory.ctime > %d " % (since)

        result = Directory._connection.queryAll(sql)
        return result

    def _list_to_inclause(categoryList):
        s = '( '
        for i in xrange(len(categoryList)):
            s += '%d' % (categoryList[i])
            if i < len(categoryList)-1:
                s += ', '
        s += ' )'
        return s
        
    try:
        since = int(since)
    except:
        return []
    categoryList = []
    for i in xrange(len(categories_requested)):
        c = lookupCategory(categories_requested[i])
        if c is None:
            continue
        categoryList.append(c.id)
    if len(categoryList) == 0:
        return []

    categorySearch = _list_to_inclause(categoryList)
    sqlresult = _rsyncFilter(categorySearch, since)
    # un-tuplelize it
    result = [d[0] for d in sqlresult]
    return result
    

class Repository(SQLObject):
    class sqlmeta:
        cacheValues = False
    name = UnicodeCol(alternateID=True, length=32)
    prefix = UnicodeCol(default=None, length=32)
    category = ForeignKey('Category')
    version = ForeignKey('Version')
    arch = ForeignKey('Arch')
    directory = ForeignKey('Directory')
    disabled = BoolCol(default=False)
    idx = DatabaseIndex('prefix', 'arch', unique=True)

def ageFileDetails():
    for d in Directory.select():
        d.age_file_details()

class FileDetail(SQLObject):
    class sqlmeta:
        cacheValues = False
    directory = ForeignKey('Directory', notNone=True)
    filename = UnicodeCol(notNone=True, length=255)
    timestamp = BigIntCol(default=None)
    size = BigIntCol(default=None)
    sha1 = UnicodeCol(default=None, length=256)
    md5 = UnicodeCol(default=None, length=32)
    sha256 = UnicodeCol(default=None, length=256)
    sha512 = UnicodeCol(default=None, length=512)

class RepositoryRedirect(SQLObject):
    class sqlmeta:
        cacheValues = False
    """ Uses strings to allow for effective named aliases, and for repos that may not exist yet """
    fromRepo = UnicodeCol(alternateID=True, length=32)
    toRepo = UnicodeCol(default=None, length=32)
    idx = DatabaseIndex('fromRepo', 'toRepo', unique=True)

class CountryContinentRedirect(SQLObject):
    class sqlmeta:
        cacheValues = False
    country = UnicodeCol(alternateID=True, notNone=True, length=32)
    continent = UnicodeCol(notNone=True, length=32)

    def _set_country(self, country):
        self._SO_set_country(country.upper())

    def _set_continent(self, continent):
        self._SO_set_continent(continent.upper())


class EmbargoedCountry(SQLObject):
    class sqlmeta:
        cacheValues = False
    country_code = StringCol(notNone=True)

class DirectoryExclusiveHost(SQLObject):
    class sqlmeta:
        cacheValues = False
    directory = ForeignKey('Directory')
    host = ForeignKey('Host')
    idx = DatabaseIndex('directory', 'host', unique=True)

###############################################################
# These classes are only used if you're not using the
# Fedora Account System or some other backend that provides
# Identity management
class Visit(SQLObject):
    class sqlmeta:
        table = "visit"

    visit_key = StringCol(length=40, alternateID=True,
                          alternateMethodName="by_visit_key")
    created = DateTimeCol(default=datetime.now)
    expiry = DateTimeCol()

    def lookup_visit(cls, visit_key):
        try:
            return cls.by_visit_key(visit_key)
        except SQLObjectNotFound:
            return None
    lookup_visit = classmethod(lookup_visit)

class VisitIdentity(SQLObject):
    visit_key = StringCol(length=40, alternateID=True,
                          alternateMethodName="by_visit_key")
    user_id = IntCol()


class Group(SQLObject):
    """
    An ultra-simple group definition.
    """

    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    class sqlmeta:
        table = "tg_group"

    group_name = UnicodeCol(length=16, alternateID=True,
                            alternateMethodName="by_group_name")
    display_name = UnicodeCol(length=255)
    created = DateTimeCol(default=datetime.now)

    # collection of all users belonging to this group
    users = RelatedJoin("User", intermediateTable="user_group",
                        joinColumn="group_id", otherColumn="user_id")

    # collection of all permissions for this group
    permissions = RelatedJoin("Permission", joinColumn="group_id", 
                              intermediateTable="group_permission",
                              otherColumn="permission_id")


class User(SQLObject):
    """
    Reasonably basic User definition. Probably would want additional attributes.
    """
    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    class sqlmeta:
        table = "tg_user"

    user_name = UnicodeCol(length=16, alternateID=True,
                           alternateMethodName="by_user_name")
    email_address = UnicodeCol(length=255, alternateID=True,
                               alternateMethodName="by_email_address")
    display_name = UnicodeCol(length=255)
    password = UnicodeCol(length=40)
    created = DateTimeCol(default=datetime.now)

    # groups this user belongs to
    groups = RelatedJoin("Group", intermediateTable="user_group",
                         joinColumn="user_id", otherColumn="group_id")

    def _get_permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    def _set_password(self, cleartext_password):
        "Runs cleartext_password through the hash algorithm before saving."
        hash = identity.encrypt_password(cleartext_password)
        self._SO_set_password(hash)

    def set_password_raw(self, password):
        "Saves the password as-is to the database."
        self._SO_set_password(password)



class Permission(SQLObject):
    permission_name = UnicodeCol(length=16, alternateID=True,
                                 alternateMethodName="by_permission_name")
    description = UnicodeCol(length=255)

    groups = RelatedJoin("Group",
                        intermediateTable="group_permission",
                         joinColumn="permission_id", 
                         otherColumn="group_id")


