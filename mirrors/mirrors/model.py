from sqlobject import *
from sqlobject.sqlbuilder import *
from turbogears import identity
import pickle
import sys
from datetime import datetime
from time import time
from string import rstrip, strip
import re
import IPy
from mirrors.lib import uniqueify
IPy.check_addr_prefixlen = 0

from turbogears.database import PackageHub


hub = PackageHub("mirrors")
__connection__ = hub

            
class SiteToSite(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    upstream_site = ForeignKey('Site')
    downstream_site = ForeignKey('Site')
    idx = DatabaseIndex('upstream_site', 'downstream_site', unique=True)

    def my_site(self):
        return self.upstream_site

class Site(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    name = UnicodeCol(alternateID=True)
    password = UnicodeCol(default=None)
    orgUrl = UnicodeCol(default=None)
    private = BoolCol(default=False)
    admin_active = BoolCol(default=True)
    user_active  = BoolCol(default=True)
    createdAt = DateTimeCol(default=datetime.utcnow())
    createdBy = UnicodeCol(default=None)
    # allow all sites to pull from me
    allSitesCanPullFromMe = BoolCol(default=False)
    downstreamComments = UnicodeCol(default=None)
    
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
        if identity.in_group("sysadmin"):
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
    #class sqlmeta:
    #    cacheValues = False
    username = UnicodeCol()
    site = ForeignKey('Site')

    def my_site(self):
        return self.site

def user_sites(identity):
    return Site.select(join=INNERJOINOn(Site, SiteAdmin, AND(SiteAdmin.q.siteID == Site.q.id,
                                                             SiteAdmin.q.username == identity.current.user_name)))


class HostCategory(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    host = ForeignKey('Host')
    category = ForeignKey('Category')
    hcindex = DatabaseIndex('host', 'category', unique=True)
    admin_active = BoolCol(default=True)
    user_active = BoolCol(default=True)
    upstream = UnicodeCol(default=None)
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
    host_category = ForeignKey('HostCategory')
    # subset of the path starting below HostCategory.path
    path = UnicodeCol()
    directory = ForeignKey('Directory')
    hcdindex = DatabaseIndex('host_category', 'path', unique=True)
    up2date = BoolCol(default=True)
    files = PickleCol(default=None)
    lastCrawled = DateTimeCol(default=None)
    

class HostCategoryUrl(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    host_category = ForeignKey('HostCategory')
    url = UnicodeCol(alternateID=True)
    private = BoolCol(default=False)

    def my_site(self):
        return self.host_category.my_site()
    
class Host(SQLObject):
    #class sqlmeta:
    #cacheValues = False
    name = UnicodeCol()
    site = ForeignKey('Site')
    idx = DatabaseIndex('site', 'name', unique=True)
    robot_email = UnicodeCol(default=None)
    admin_active = BoolCol(default=True)
    user_active = BoolCol(default=True)
    country = StringCol(default=None)
    bandwidth = UnicodeCol(default=None)
    bandwidth_int = IntCol(default=100)
    comment = UnicodeCol(default=None)
    _config = PickleCol(default=None)
    lastCheckedIn = DateTimeCol(default=None)
    lastCrawled = DateTimeCol(default=None)
    private = BoolCol(default=False)
    internet2 = BoolCol(default=False)
    internet2_clients = BoolCol(default=False)
    countries_allowed = MultipleJoin('HostCountryAllowed')
    netblocks = MultipleJoin('HostNetblock', orderBy='netblock')
    acl_ips = MultipleJoin('HostAclIp', orderBy='ip')
    categories = MultipleJoin('HostCategory')

    def destroySelf(self):
        """Cascade the delete operation"""
        s = [self.countries_allowed,
             self.netblocks,
             self.acl_ips,
             self.categories]
        for a in s:
            for b in a:
                b.destroySelf()
        SQLObject.destroySelf(self)



    def _uploaded_config(self, config):
        message = ''

        def _config_categories(config):
            noncategories = ['version', 'global', 'site', 'host', 'stats']
            if config is not None:
                return [key for key in config.keys() if key not in noncategories]
            else:
                return []


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
                for k,v in config[c]['dirtree'].iteritems():
                    d = strip(k, '/')
                    hcdir = HostCategoryDir.selectBy(host_category = hc, path=d)
                    if hcdir.count() > 0:
                        hcdir = hcdir[0]
                        # don't store files, we don't need it right now
                        # hcdir.files = None
                        is_up2date=False
                        if len(v) > 0:
                            is_up2date=True
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

def _publiclist_hosts(product, re):
    productId = product.id
    sql = "SELECT host.id "
    sql += "FROM category, host_category, host_category_dir, host, site "
    # join conditions
    sql += "WHERE "
    sql += "host_category.category_id = category.id AND "
    sql += "host_category.host_id = host.id AND "
    sql += "host_category_dir.host_category_id = host_category.id AND "
    sql += "category.product_id = %s AND " % productId
    sql += "host.site_id = site.id "
    # select conditions
    # up2date, active, not private
    sql += 'AND (host_category_dir.up2date OR host_category.always_up2date) '
    sql += 'AND host.user_active AND site.user_active '
    sql += 'AND host.admin_active AND site.admin_active '
    sql += 'AND NOT host.private '
    sql += 'AND NOT site.private '

    if re is not None:
        sql += "AND host_category_dir.path ~ '%s' " % re
    sql += "ORDER BY host.country "

    result = product._connection.queryAll(sql)
    result = uniqueify(result)
    return result


def publiclist_hosts(productname, vername, archname):
        """ has a category of product, and an hcd that matches version """
        try:
            product = Product.byName(productname)
        except SQLObjectNotFound:
            return False
        if vername is not None and archname is not None:
            desiredPath = '(^|/)%s/.*%s/' % (vername, archname)
        elif vername is not None:
            desiredPath = '(^|/)%s/' % vername
        else:
            desiredPath = None

        sqlresult = _publiclist_hosts(product, desiredPath)
        return sqlresult


class HostAclIp(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    host = ForeignKey('Host')
    ip = UnicodeCol()

    def my_site(self):
        return self.host.my_site()

def _rsync_acl_list(dbobject, internet2_only, public_only):
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

    result = dbobject._connection.queryAll(sql)
    return result

def rsync_acl_list(internet2_only=False,public_only=False):
    d = Directory.select()[0]
    result = _rsync_acl_list(d, internet2_only, public_only)
    return [t[0] for t in result]

class HostCountryAllowed(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    host = ForeignKey('Host')
    country = StringCol(notNone=True)

    def my_site(self):
        return self.host.my_site()

class HostNetblock(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    host = ForeignKey('Host')
    netblock = StringCol()

    def my_site(self):
        return self.host.my_site()


class HostStats(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    host = ForeignKey('Host')
    _timestamp = DateTimeCol(default=datetime.utcnow())
    type = UnicodeCol(default=None)
    data = PickleCol(default=None)


class Arch(SQLObject):
    name = UnicodeCol(alternateID=True)

primary_arches = ['i386','x86_64','ppc']
display_publiclist_arches = primary_arches + ['ia64', 'sparc']

# e.g. 'fedora' and 'epel'
class Product(SQLObject):
    name = UnicodeCol(alternateID=True)
    versions = MultipleJoin('Version', orderBy='name')
    categories = MultipleJoin('Category')

    def destroySelf(self):
        for v in self.versions:
            v.destroySelf()
        for c in self.categories:
            c.destroySelf()
        SQLObject.destroySelf(self)
        

class Version(SQLObject):
    name = UnicodeCol()
    product = ForeignKey('Product')
    isTest = BoolCol(default=False)
    display = BoolCol(default=True)
    display_name = UnicodeCol(default=None)
    ordered_mirrorlist = BoolCol(default=True)


class Directory(SQLObject):
    # Full path
    # e.g. pub/fedora/linux/core/6/i386/os
    # e.g. pub/fedora/linux/extras
    # e.g. pub/epel
    # e.g. pub/fedora/linux
    name = UnicodeCol(alternateID=True)
    files = PickleCol(default={})
    readable = BoolCol(default=True)
    categories = RelatedJoin('Category')
    repository = SingleJoin('Repository') # zero or one repository, set if this dir contains a yum repo
    host_category_dirs = MultipleJoin('HostCategoryDir')
    fileDetails = MultipleJoin('FileDetail')

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
        SQLObject.destroySelf(self)

    def age_file_details(self):
        """Keep at least 1 FileDetail entry, removing any others
        that are more than 7 days old."""
        weekago = int(time.time()) - (60*60*24*7)
        latest = None
        latest_timestamp = 0
        if len(fileDetails) > 1:
            for f in fileDetails:
                if f.timestamp > latest_timestamp:
                    latest=f
                    latest_timestamp=f.timestamp
            for f in fileDetails:
                if f != latest and f.timestamp < weekago:
                    f.destroySelf()


class Category(SQLObject):
    #class sqlmeta:
    #    cacheValues = False
    # Top-level mirroring
    # e.g. core, extras, release, epel
    name = UnicodeCol(alternateID=True)
    product = ForeignKey('Product')
    canonicalhost = UnicodeCol(default='http://download.fedora.redhat.com')
    topdir = ForeignKey('Directory', default=None)
    publiclist = BoolCol(default=True)
    directories = RelatedJoin('Directory', orderBy='name') # all the directories that are part of this category
    hostCategories = MultipleJoin('HostCategory')

    def destroySelf(self):
        for hc in self.hostCategories:
            hc.destroySelf()
        SQLObject.destroySelf(self)

class Repository(SQLObject):
    name = UnicodeCol(alternateID=True)
    prefix = UnicodeCol(default=None)
    category = ForeignKey('Category')
    version = ForeignKey('Version')
    arch = ForeignKey('Arch')
    directory = ForeignKey('Directory')
    disabled = BoolCol(default=False)

def ageFileDetails():
    for d in Directory.select():
        d.age_file_details()

class FileDetail(SQLObject):
    directory = ForeignKey('Directory', notNone=True)
    filename = UnicodeCol(notNone=True)
    timestamp = DateTimeCol(default=None)
    size = IntCol(default=0)
    sha1 = UnicodeCol(default=None)
    md5 = UnicodeCol(default=None)
    # fixme maybe - this will force uniqueness for dir/file combinations
    # without regard to historical data (e.g. slightly stale mirrors)
    # which we may have to actually deal with properly
    idx = DatabaseIndex('directory', 'filename', unique=True)

class RepositoryRedirect(SQLObject):
    """ Uses strings to allow for effective named aliases, and for repos that may not exist yet """
    fromRepo = UnicodeCol(alternateID=True)
    toRepo = UnicodeCol(default=None)
    idx = DatabaseIndex('fromRepo', 'toRepo', unique=True)

class CountryContinentRedirect(SQLObject):
    country = UnicodeCol(alternateID=True, notNone=True)
    continent = UnicodeCol(notNone=True)

    def _set_country(self, country):
        self._SO_set_country(country.upper())

    def _set_continent(self, continent):
        self._SO_set_continent(continent.upper())


class EmbargoedCountry(SQLObject):
    country_code = StringCol(notNone=True)


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


