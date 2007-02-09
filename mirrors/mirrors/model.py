from sqlobject import *
from sqlobject.sqlbuilder import *
from turbogears import identity
import pickle
import sys

from turbogears.database import PackageHub


hub = PackageHub("mirrors")
__connection__ = hub

            
class SiteToSite(SQLObject):
    upstream_site = ForeignKey('Site')
    downstream_site = ForeignKey('Site')
    idx = DatabaseIndex('upstream_site', 'downstream_site', unique=True)

    def my_site(self):
        return self.upstream_site

class Site(SQLObject):
    name = StringCol(alternateID=True)
    password = StringCol(default=None)
    orgUrl = StringCol(default=None)
    private = BoolCol(default=False)
    admin_active = BoolCol(default=True)
    user_active  = BoolCol(default=True)
    admins = MultipleJoin('SiteAdmin')
    hosts  = MultipleJoin('Host')

    def destroySelf(self):
        """Cascade the delete operation"""
        for h in self.hosts:
            h.destroySelf()
        for a in self.admins:
            a.destroySelf()
        for s in SiteToSite.select(OR(SiteToSite.q.upstream_siteID == self,
                                        SiteToSite.q.downstream_siteID == self)):
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
        

class SiteAdmin(SQLObject):
    username = StringCol()
    site = ForeignKey('Site')

    def my_site(self):
        return self.site

def user_sites(identity):
    return Site.select(join=INNERJOINOn(Site, SiteAdmin, AND(SiteAdmin.q.siteID == Site.q.id,
                                                             SiteAdmin.q.username == identity.current.user_name)))


class HostCategory(SQLObject):
    host = ForeignKey('Host')
    category = ForeignKey('Category')
    hcindex = DatabaseIndex('host', 'category', unique=True)
    admin_active = BoolCol(default=True)
    user_active = BoolCol(default=True)
    path = StringCol()
    upstream = StringCol(default=None)
    dirtree = PickleCol(default=None)
    urls = MultipleJoin('HostCategoryUrl')

    def destroySelf(self):
        """Cascade the delete operation"""
        for b in urls:
            b.destroySelf()
        SQLObject.destroySelf(self)

    def my_site(self):
        return self.host.my_site()

class HostCategoryUrl(SQLObject):
    host_category = ForeignKey('HostCategory')
    url = StringCol(alternateID=True)
    private = BoolCol(default=False)

    def my_site(self):
        return self.host_category.my_site()
    
class Host(SQLObject):
    name = StringCol()
    site = ForeignKey('Site')
    idx = DatabaseIndex('site', 'name', unique=True)
    robot_email = StringCol(default=None)
    admin_active = BoolCol(default=True)
    user_active = BoolCol(default=True)
    country = StringCol(default=None)
    _config = PickleCol(default=None)
    _timestamp = DateTimeCol(default=None)
    private = BoolCol(default=False)
    countries_allowed = MultipleJoin('HostCountryAllowed')
    netblocks = MultipleJoin('HostNetblock')
    acl_ips = MultipleJoin('HostAclIp')
    categories = MultipleJoin('HostCategory')
    mirrors = MultipleJoin('MirrorDirectory')

    def destroySelf(self):
        """Cascade the delete operation"""
        s = [self.countries_allowed,
             self.netblocks,
             self.acl_ips,
             self.categories,
             self.mirrors]
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
            if config[c].has_key('path'):
                path = config[c]['path']
            else:
                path = None
            hc = HostCategory.selectBy(host=self, category=category)
            if hc.count() > 0:            
                hc = hc[0]
            else:
                hc = HostCategory(host=self, category=category, path=path)
            if path is not None:
                hc.path = path
            if config[c].has_key('user_active'):
                hc.user_active = config[c]['user_active']
            if config[c].has_key('upstream'):
                hc.upstream = config[c]['upstream']
            if config[c].has_key('dirtree'):
                hc.dirtree = config[c]['dirtree']
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
        return self.admin_active and self.site.admin_active

    def is_active(self):
        return self.admin_active and self.user_active and self.site.user_active
    
    def _get_config(self):
        return self._config

    def _set_config(self, config):
        self._config = config
        self._timestamp = DateTimeCol.now()
        self._uploaded_config(config)

    def _get_timestamp(self):
        return self._timestamp

    def has_category_dir(self, cname, dir):
        try:
            for hc in HostCategory.selectBy(host=self, category=Category.byName(cname)):
                return hc.dirtree.has_key(dir)
        except:
            return False

    def my_site(self):
        return self.site

class HostAclIp(SQLObject):
    host = ForeignKey('Host')
    ip = StringCol()

    def my_site(self):
        return self.host.my_site()

class HostCountryAllowed(SQLObject):
    host = ForeignKey('Host')
    country = StringCol()

    def my_site(self):
        return self.host.my_site()

class HostNetblock(SQLObject):
    host = ForeignKey('Host')
    netblock = StringCol()

    def my_site(self):
        return self.host.my_site()
    

def category_mirrors(category):
    result = []
    # pub/fedora/linux/core
    topdir = category.directory.name
    for h in Host.select():
        if h.has_category(category.name):
            result.append(h)
    return result


def directory_mirrors(dirname, country=None, include_private=False):
    """Given a directory like pub/fedora/linux/core/5/i386/os,
    what active hosts have this directory?  To find that,
    we need to know the category the directory falls under,
    then need to look up each host to see if it has that category,
    and if so, if it has that directory under the category."""
    origdir = dirname
    result = []
    category = None
    while category is None and len(dirname) > 0:
        try:
            d = Directory.byName(dirname)
        except SQLObjectNotFound:
            return result
        if len(d.category) > 0:
            category = d.category[0]
            break
        else:
            dirname = dirname.split('/')[:-1]
            dirname = '/'.join(dirname)
            
    if category is None:
        return None

    dirname = origdir[len(category.directory.name)+1:]
    print dirname

    hosts = category_mirrors(category)
    for h in hosts:
        if h.is_active() and h.has_category_dir(category.name, dirname):
            if h.private and not include_private:
                continue
            result.append((category.name, dirname, h))
    return result

def directory_mirror_urls(dname, country=None, include_private=False):
    result = []
    for cname, dirname, host in directory_mirrors(dname, include_private):
        if not host.is_active():
            continue
        if host.private and not include_private:
            continue
        for u in host.category_urls(cname):
            result.append('%s/%s' % (u, dirname))
    return result


class HostStats(SQLObject):
    host = ForeignKey('Host')
    _timestamp = DateTimeCol(default=None)


class Arch(SQLObject):
    name = StringCol(alternateID=True)

# e.g. 'fedora' and 'rhel'
class Product(SQLObject):
    name = StringCol(alternateID=True)
    versions = MultipleJoin('Version')
    categories = MultipleJoin('Category')

class Version(SQLObject):
    name = StringCol()
    product = ForeignKey('Product')
    isTest = BoolCol(default=False)


class Directory(SQLObject):
    # Full path
    # e.g. pub/fedora/linux/core/6/i386/os
    # e.g. pub/fedora/linux/extras
    # e.g. pub/epel
    # e.g. pub/fedora/linux/release
    name = StringCol(alternateID=True)
    repository = MultipleJoin('Repository')
    mirrors = MultipleJoin('MirrorDirectory')
    category = MultipleJoin('Category')


class Category(SQLObject):
    # Top-level mirroring
    # e.g. core, extras, release, epel
    name = StringCol(alternateID=True)
    product = ForeignKey('Product')
    canonicalhost = StringCol(default='http://download.fedora.redhat.com')
    directory = ForeignKey('Directory')


class Repository(SQLObject):
    name = StringCol(alternateID=True)
    shortname = StringCol(default=None)
    category = ForeignKey('Category')
    version = ForeignKey('Version')
    arch = ForeignKey('Arch')
    directory = ForeignKey('Directory')
    shortnameIndex = DatabaseIndex('shortname')

class MirrorDirectory(SQLObject):
    """To cache lookups"""
    host = ForeignKey('Host')
    directory = ForeignKey('Directory')

class EmbargoedCountry(SQLObject):
    country_code = StringCol()


from turbogears import identity 
from datetime import datetime

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

    mirrors = MultipleJoin("Mirror")

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


