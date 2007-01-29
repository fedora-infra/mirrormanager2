from sqlobject import *
import pickle
import sys

from turbogears.database import PackageHub


hub = PackageHub("mirrors")
__connection__ = hub

class Site(SQLObject):
    name = StringCol(alternateID=True)
    password = StringCol(default=None)
    orgUrl = StringCol(default=None)
    private = BoolCol(default=False)
    admin_active = BoolCol(default=True)
    user_active  = BoolCol(default=True)
    admins = MultipleJoin('SiteAdmin')
    hosts  = MultipleJoin('Host')

    def delete(self):
        """Cascade the delete operation"""
        for h in self.hosts:
            h.destroySelf()
        for a in self.admins:
            a.destroySelf()
        self.destroySelf()

class SiteAdmin(SQLObject):
    username = StringCol()
    site = ForeignKey('Site')

class Host(SQLObject):
    name = StringCol()
    site = ForeignKey('Site')
    robot_email = StringCol(default=None)
    admin_active = BoolCol(default=True)
    user_active = BoolCol(default=True)
    _country = StringCol(default=None)
    _config = PickleCol(default=None)
    _timestamp = DateTimeCol(default=None)
    mirrors = MultipleJoin('MirrorDirectory')

    def is_admin_active(self):
        return self.admin_active and self.site.admin_active

    def is_active(self):
        return self.admin_active and self.user_active and self.site.user_active
    

    def _get_config(self):
        return self._config

    def _set_config(self, config):
        self._config = config
        self._timestamp = DateTimeCol.now()

    def _get_timestamp(self):
        return self._timestamp

    # virtual attributes grabbed from the config
    def _get_private(self):
        if self._config is not None and self._config.has_key('host'):
            if self._config['host'].has_key('private'):
                return self._config['host']['private'] == '1'
        return False

    def _get_country(self):
        if self._config is not None and self._config.has_key('host'):
            if self._config['host'].has_key('country'):
                return self._config['host']['country']
            else:
                return self._country
        return None

    def _get_countries_allowed(self):
        if self._config is not None and self._config.has_key('host'):
            if self._config['host'].has_key('countries_allowed'):
                return self._config['host']['countries_allowed']
        return None
        
    def _get_netblocks(self):
        if self._config is not None and self._config.has_key('host'):
            if self._config['host'].has_key('netblocks'):
                return self._config['host']['netblocks']
        return None

    def _get_private_rsync(self):
        if self._config is not None and self._config.has_key('host'):
            if self._config['host'].has_key('private_rsync'):
                return self._config['host']['private_rsync']
        return None

    def _get_acl_ips(self):
        if self._config is not None and self._config.has_key('host'):
            if self._config['host'].has_key('acl_ips'):
                return self._config['host']['acl_ips']
        return None

    def _get_categories(self):
        noncategories = ['global', 'site', 'host', 'stats']
        result = []
        for key in self._config.keys():
            if key not in noncategories:
                result.append(key)
        return result

    def has_category(self, category):
        return self._config.has_key(category)

    def category_enabled(self, category):
        return self._config[category]['enabled'] == '1'

    def category_path(self, category):
        return self._config[category]['path']

    def category_urls(self, category):
        urls = self._config[category]['urls']
        if type(urls) == list:
            return urls
        elif type(urls) == str:
            return [urls]
    
    def category_upstream(self, category):
        return self._config[category]['upstream']

    def category_dirtree(self, category):
        return self._config[category]['dirtree']

    def category_dir(self, category, dir):
        return self._config[category]['dirtree'].has_key(dir)


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


