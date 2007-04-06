from sqlobject import *
from sqlobject.sqlbuilder import *
from turbogears import identity
import pickle
import sys
from datetime import datetime
from string import rstrip, strip
import re

from turbogears.database import PackageHub


hub = PackageHub("mirrors")
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
    name = UnicodeCol(alternateID=True)
    password = UnicodeCol(default=None)
    orgUrl = UnicodeCol(default=None)
    private = BoolCol(default=False)
    admin_active = BoolCol(default=True)
    user_active  = BoolCol(default=True)
    createdAt = DateTimeCol(default=datetime.utcnow())
    createdBy = UnicodeCol(default=None)
    licensesAccepted  = BoolCol(default=False)
    licensesAcceptedAt = DateTimeCol(default=datetime.utcnow())
    licensesAcceptedBy = UnicodeCol(default=None)
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
        return [s2s.downstream_site for s2s in SiteToSite.selectBy(upstream_site=self)]

    def _get_upstream_sites(self):
        return [s2s.upstream_site for s2s in SiteToSite.selectBy(downstream_site=self)]

    def add_downstream_site(self, site):
        if site is not None:
            SiteToSite(upstream_site=self, downstream_site=site)

    def del_downstream_site(self, site):
        for s in SiteToSite.selectBy(upstream_site=self, downstream_site=site):
            s.destroySelf()
        

    def is_siteadmin(self, identity):
        if identity.in_group("sysadmin"):
            return True
        for a in self.admins:
            if a.username == identity.current.user_name:
                return True
        return False

    def is_downstream_siteadmin(self, identity):
        """If you are a sysadmin of one of my immediate downstream sites,
        you can see some of my site details, but you can't edit them.
        """
        for d in self.downstream_sites:
            for a in d.admins:
                if a.username == identity.current.user_name:
                    return True
        return False

    def is_downstream_siteadmin_byname(self, name):
        for d in self.downstream_sites:
            for a in d.admins:
                if a.username == name:
                    return True
        return False

    def accept_licenses(self, identity):
        self.licensesAcceptedBy = identity.current.user_name
        self.licensesAcceptedAt = datetime.utcnow()
        self.licensesAccepted = True

        

class SiteAdmin(SQLObject):
    class sqlmeta:
        cacheValues = False
    username = UnicodeCol()
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
    upstream = UnicodeCol(default=None)
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
    hcdindex = DatabaseIndex('host_category', 'path', unique=True)
    up2date = BoolCol(default=True)
    files = PickleCol(default=None)
    lastCrawled = DateTimeCol(default=None)
    

class HostCategoryUrl(SQLObject):
    class sqlmeta:
        cacheValues = False
    host_category = ForeignKey('HostCategory')
    url = UnicodeCol(alternateID=True)
    private = BoolCol(default=False)

    def my_site(self):
        return self.host_category.my_site()
    
class Host(SQLObject):
    class sqlmeta:
        cacheValues = False
    name = UnicodeCol()
    site = ForeignKey('Site')
    idx = DatabaseIndex('site', 'name', unique=True)
    robot_email = UnicodeCol(default=None)
    admin_active = BoolCol(default=True)
    user_active = BoolCol(default=True)
    country = StringCol(default=None)
    bandwidth = UnicodeCol(default=None)
    comment = UnicodeCol(default=None)
    _config = PickleCol(default=None)
    lastCheckedIn = DateTimeCol(default=None)
    private = BoolCol(default=False)
    countries_allowed = MultipleJoin('HostCountryAllowed')
    netblocks = MultipleJoin('HostNetblock')
    acl_ips = MultipleJoin('HostAclIp')
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

    def _get_config_categories(self):
        noncategories = ['version', 'global', 'site', 'host', 'stats']
        return [key for key in self._config.keys() if key not in noncategories]


    def _uploaded_config(self, config):
        if config['site'].has_key('user_active'):
            self.site.user_active = config['site']['user_active']
        if config['host'].has_key('country'):
            self.country = config['host']['country']
        if config['host'].has_key('private'):
            self.private = config['host']['private']
        if config['host'].has_key('robot_email'):
            self.robot_email = config['host']['robot_email']
        if config['host'].has_key('user_active'):
            self.user_active = config['host']['user_active']
        self.site.sync()
        self.sync()

        if config['host'].has_key('acl_ips'):
            if type(config['host']['acl_ips']) == list:
                data = config['host']['acl_ips']
            else:
                data = [config['host']['acl_ips']]
            for a in data:
                if HostAclIp.selectBy(host=self, ip=a).count() == 0:
                    HostAclIp(host=self, ip=a)
            for h in HostAclIp.selectBy(host=self):
                if h.ip not in data:
                    h.destroySelf()

        if config['host'].has_key('countries_allowed'):
            if type(config['host']['countries_allowed']) == list:
                data = config['host']['countries_allowed']
            else:
                data = [config['host']['countries_allowed']]
            for a in data:
                if HostCountryAllowed.selectBy(host=self, country=a).count() == 0:
                    HostCountryAllowed(host=self, country=a)
            for h in HostCountryAllowed.selectBy(host=self):
                if h.country not in data:
                    h.destroySelf()

        if config['host'].has_key('netblocks'):
            if type(config['host']['netblocks']) == list:
                data = config['host']['netblocks']
            else:
                data = [config['host']['netblocks']]
            for a in data:
                if HostNetblock.selectBy(host=self, netblock=a).count() == 0:
                    HostNetblock(host=self, netblock=a)
            for h in HostNetblock.selectBy(host=self):
                if h.netblock not in data:
                    h.destroySelf()

        # now fill in the host category data (HostCategory and HostCategoryURL)
        for c in self.config_categories:
            category = Category.selectBy(name=c)
            if category.count() > 0:
                category = category[0]
            else: # not a category the database knows about, ignore it
                continue
            if not config[c].has_key('enabled') or config[c]['enabled'] != '1':
                continue
            hc = HostCategory.selectBy(host=self, category=category)
            if hc.count() > 0:            
                hc = hc[0]
            else:
                hc = HostCategory(host=self, category=category)
            if config[c].has_key('user_active'):
                hc.user_active = config[c]['user_active']
            if config[c].has_key('upstream'):
                hc.upstream = config[c]['upstream']

            # and now one HostCategoryDir for each dir in the dirtree
            if config[c].has_key('dirtree'):
                for d in config[c]['dirtree'].keys():
                    d = strip(d, '/')
                    hcdir = HostCategoryDir.selectBy(host_category = hc, path=d)
                    if hcdir.count() > 0:
                        hcdir = hcdir[0]
                        hcdir.files = config[c]['dirtree'][d]
                        hcdir.up2date = True
                        hcdir.sync()
                    else:
                        hcdir = HostCategoryDir(host_category=hc, path=d, files=config[c]['dirtree'][d])
                for d in HostCategoryDir.selectBy(host_category=hc):
                    if d.path not in config[c]['dirtree'].keys():
                        d.destroySelf()

            hc.sync()

            if config[c].has_key('urls'):
                urls = config[c]['urls']
                if type(urls) != list:
                    urls = [urls]
                for u in urls:
                    if HostCategoryUrl.selectBy(host_category=hc,
                                                url=u,
                                                private=False).count() == 0:
                        HostCategoryUrl(host_category=hc, url=u,
                                        private=False)
                    for hcurl in HostCategoryUrl.selectBy(host_category=hc, private=False):
                        if hcurl.url not in urls:
                            hcurl.destroySelf()
                                                          
            if config[c].has_key('private_urls'):
                urls = config[c]['private_urls'];
                if type(urls) != list:
                    urls = [urls]
                for u in urls:
                    if HostCategoryUrl.selectBy(host_category=hc,
                                                url=u,
                                                private=True).count() == 0:
                        HostCategoryUrl(host_category=hc, url=u,
                                        private=True)
                    for hcurl in HostCategoryUrl.selectBy(host_category=hc, private=True):
                        if hcurl.url not in urls:
                            hcurl.destroySelf()
            
                                                          


    def is_admin_active(self):
        return self.admin_active and self.site.admin_active and self.site.licensesAccepted

    def is_active(self):
        return self.admin_active and self.user_active and self.site.user_active

    def is_private(self):
        return self.private or self.site.private
    
    def _get_config(self):
        return self._config

    def _set_config(self, config):
        self._config = config
        self.lastCheckedIn = datetime.utcnow()
        self._uploaded_config(config)

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

    def product_version_arch_dirs(self, productname, vername, archname):
        """ has a category of product, and an hcd that matches version """
        result = []
        try:
            product = Product.byName(productname)
        except SQLObjectNotFound:
            return result
        if vername is not None and archname is not None:
            desiredPath = '(^|/)%s/.*%s/' % (vername, archname)
        elif vername is not None:
            desiredPath = '(^|/)%s/' % vername
        else:
            desiredPath = '.*'
            
        r = re.compile(desiredPath)
        for hc in self.categories:
            if productname == hc.category.product.name:
                for hcd in hc.dirs:
                    if r.search(hcd.path):
                        result.append(hcd)
        return result
        


class HostAclIp(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    ip = UnicodeCol()

    def my_site(self):
        return self.host.my_site()

class HostCountryAllowed(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    country = StringCol()

    def my_site(self):
        return self.host.my_site()

class HostNetblock(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    netblock = StringCol()

    def my_site(self):
        return self.host.my_site()
    

def category_mirrors(category):
    return [hc.host for hc in HostCategory.selectBy(category=category)]


def _directory_mirrors(directory, country):

    sql = "SELECT category.id, host_category.id, host.id "
    sql += "FROM category, host_category, host "
    sql += "WHERE category.id = host_category.category_id AND "
    sql += "host_category.host_id = host.id "
    if country is not '':
        country = country.upper()
        sql += "AND host.country = '%s' " % country
    sql += "ORDER BY host.id"
    
    result = directory._connection.queryAll(sql)
    return result


def directory_mirrors(directory, country='', include_private=False):
    """Given a directory like pub/fedora/linux/core/5/i386/os,
    what active hosts have this directory?  To find that,
    we need to know the category the directory falls under,
    then need to look up each host to see if it has that category,
    and if so, if it has that directory under the category."""
    origdir = directory.name
    result = []
    category = None
    if country is None: country=''
    if country.upper() == u'GLOBAL':
        country = ''

    d = directory

    if len(d.categories) == 0:
        return result

    dm = _directory_mirrors(d, country)
    for categoryId, hostcategoryId, hostId in dm:
        host = Host.get(hostId)
        if host.is_private() and not include_private:
            continue
        category = Category.get(categoryId)
        # dirname is the subpath starting below the category's top-level directory
        dirname = origdir[len(category.topdir.name)+1:]
        hcd_exists = host.has_category_dir(category, dirname)
        if host.is_active() and hcd_exists:
            result.append((category.name, dirname, host))
    return result

def directory_mirror_urls(directory, country='', include_private=False):
    result = []
    for cname, dirname, host in directory_mirrors(directory, country, include_private):
        for u in host.category_urls(cname):
            fullurl = '%s/%s' % (u, dirname)
            cc = host.country
            if cc: cc = cc.upper()
            else: cc=''
            result.append((fullurl, cc))
    return result


class HostStats(SQLObject):
    class sqlmeta:
        cacheValues = False
    host = ForeignKey('Host')
    _timestamp = DateTimeCol(default=datetime.utcnow())
    type = UnicodeCol(default=None)
    data = PickleCol(default=None)


class Arch(SQLObject):
    name = UnicodeCol(alternateID=True)

primary_arches = ['i386','x86_64','ppc']

# e.g. 'fedora' and 'rhel'
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


class Directory(SQLObject):
    # Full path
    # e.g. pub/fedora/linux/core/6/i386/os
    # e.g. pub/fedora/linux/extras
    # e.g. pub/epel
    # e.g. pub/fedora/linux/release
    name = UnicodeCol(alternateID=True)
    files = PickleCol(default={})
    categories = RelatedJoin('Category')
    repository = SingleJoin('Repository') # zero or one repository, set if this dir contains a yum repo

    def destroySelf(self):
        if self.repository is not None:
            self.repository.destroySelf()
        # don't destroy a whole category if only deleting a directory
        SQLObject.destroySelf(self)
    


class Category(SQLObject):
    class sqlmeta:
        cacheValues = False
    # Top-level mirroring
    # e.g. core, extras, release, epel
    name = UnicodeCol(alternateID=True)
    product = ForeignKey('Product')
    canonicalhost = UnicodeCol(default='http://download.fedora.redhat.com')
    topdir = ForeignKey('Directory', default=None)
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

class EmbargoedCountry(SQLObject):
    country_code = StringCol()


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


