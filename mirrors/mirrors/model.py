from sqlobject import *

from turbogears.database import PackageHub


hub = PackageHub("mirrors")
__connection__ = hub

from mirrors.identity_models import *

class Site(SQLObject):
    name = StringCol(alternateID=True)
    robot_email = StringCol(default=None)
    upload_password = StringCol(default=None)
    admin_active = BoolCol(default=False)
    user_active = BoolCol(default=True)
    private = BoolCol(default=False)
    admins = MultipleJoin('SiteAdmin')
    hosts  = MultipleJoin('Host')
    ips    = MultipleJoin('SiteIP')
    

class SiteAdmin(SQLObject):
    username = StringCol()
    site = ForeignKey('Site')

# IP addresses to go in the rsync ACLs
class SiteIP(SQLObject):
    site = ForeignKey('Site')
    address = StringCol()

class Host(SQLObject):
    name = StringCol()
    site = ForeignKey('Site')
    country = StringCol(default=None)
    internet2 = BoolCol(default=False)
    pull_from = ForeignKey('Site')
    mirrors = MultipleJoin('MirrorDirectory')
    private_rsyncs = MultipleJoin('HostPrivateRsync')
    ip_blocks = MultipleJoin('HostIPBlocks')
    hostFile = MultipleJoin('HostFile')
    categories = MultipleJoin('HostCategory')
    
# the listings are kept in the file system
class HostFile(SQLObject):
    host = ForeignKey('Host')
    type = StringCol()
    timestamp = DateTimeCol(default=DateTimeCol.now)

    def listingFilename(self):
        return 'hostfiles/host-%s-%s.jpg' % (self.host.id, self.type) # fixme, only one file of each type??

    def _get_listing(self):
        if not os.path.exists(self.listingFilename()):
            return None
        f = open(self.listingFilename())
        v = f.read()
        f.close()
        return v

    def _set_listing(self, value):
        # assume we get a string for the listing
        f = open(self.listingFilename(), 'w')
        f.write(value)
        f.close()

    def _del_listing(self, value):
        # I usually wouldn't include a method like this, but for
        # instructional purposes...
        os.unlink(self.listingFilename())


# for other mirrors to pull from in tiering
class HostPrivateRsync(SQLObject):
    host = ForeignKey('Host')
    url = StringCol()
    user = StringCol(default=None)
    password = StringCol(default=None)

# some hosts only serve some IP CIDR blocks
# such as private mirrors behind
# company firewalls.  This lets them first try
# the global yum mirrorlist redirector which will
# return them their local mirror URL
class HostIPBlocks(SQLObject):
    host = ForeignKey('Host')
    cidr    = StringCol()


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


# Directories are all from the perspective of the
# master download server.
class DirectoryTree(SQLObject):
    parent = ForeignKey('Directory')
    child  = ForeignKey('Directory')

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
    category = ForeignKey('Category')
    version = ForeignKey('Version')
    arch = ForeignKey('Arch')
    directory = ForeignKey('Directory')


class HostCategory(SQLObject):
    host     = ForeignKey('Host')
    category = ForeignKey('Category')
    hcURLs   = MultipleJoin('HostCategoryURL')
    

# One per protocol/path one can get at this same data
# checking one HostCategoryURL is the same as checking them all
class HostCategoryURL(SQLObject):
    hostcategory = ForeignKey('HostCategory')
    protocol = StringCol(default='http://')
    # The equivalent of the dir structure on the masters
    # e.g. 'core' -> 'pub/fedora/linux/core'
    path = StringCol()
    # using protocol + host.name + path, we get a
    # full URL to same, e.g. 'http://download.fedoraproject.org/pub/fedora/linux/core'
    def _get_url(self):
        return '%s%s/%s' % (self.protocol, self.host.name, self.path)



# one per Host per Directory
# fortunately these will be created/modified
# by a crawler program rather than manually
class MirrorDirectory(SQLObject):
    directory = ForeignKey('Directory')
    host = ForeignKey('Host')
    url = ForeignKey('HostCategoryURL')
    # this is the path below url.path
    path = StringCol()
    # sync status
    synced = BoolCol(default=False)
    lastChecked = DateTimeCol(default=DateTimeCol.now)

