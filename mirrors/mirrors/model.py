from sqlobject import *

from turbogears.database import PackageHub


hub = PackageHub("mirrors")
__connection__ = hub

from mirrors.identity_models import *

class Site(SQLObject):
    name = StringCol(alternateID=True)
    robot_email = StringCol(default=None)
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
    mirrors = MultipleJoin('Mirror')
    private_rsyncs = MultipleJoin('HostPrivateRsync')
    ip_blocks = MultipleJoin('HostIPBlocks')

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


class Content(SQLObject):
    # e.g. fedora-core-6-i386
    name = StringCol(alternateID=True)
    # e.g. core, extras, updates, updates-testing, test, ...
    category = StringCol()
    # 5, 6, development
    version = StringCol()
    # default subdir starting below /
    # e.g. 'pub/fedora/core/6/$ARCH/'
    path = StringCol()
    canonical = StringCol()
    arch      = ForeignKey('Arch')
    # these are paths below $ARCH/
    # e.g. iso/, os/, debuginfo/
    # of course Extras doesn't have these ;-(
    isos  = StringCol(default=None)
    binarypackages  = StringCol(default=None)
    repodata  = StringCol(default=None)
    debuginfo = StringCol(default='debug/')
    repoview  = StringCol(default=None)
    mirrors = MultipleJoin('Mirror')

# one per Host per Content
# fortunately these will be created/modified
# by a crawler program rather than manually
class Mirror(SQLObject):
    host = ForeignKey('Host')
    content  = ForeignKey('Content')
    urls = MultipleJoin('MirrorURL')
    # sync status
    dvd_isos_synced    = BoolCol(default=False)
    cd_isos_synced     = BoolCol(default=False)
    binarypackages_synced  = BoolCol(default=False)
    debuginfo_synced = BoolCol(default=False)
    repoview_synced  = BoolCol(default=False)

# One per protocol/path one can get at this same data
# checking one MirrorURL is the same as checking them all
class MirrorURL(SQLObject):
    mirror = ForeignKey('Mirror')
    # The equivalent of the dir structure on the masters
    # e.g. http://mirrors.kernel.org/fedora/core/6/i386/os/
    path      = StringCol(default=None)
