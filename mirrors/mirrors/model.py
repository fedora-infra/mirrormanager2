from sqlobject import *

from turbogears.database import PackageHub


hub = PackageHub("mirrors")
__connection__ = hub

# class YourDataClass(SQLObject):
#     pass

from mirrors.identity_models import *

class Config(SQLObject):
    release = MultipleJoin('Release')

class Release(SQLObject):
    name = StringCol(alternateID=True)
    canonical = StringCol()
    comment = StringCol()
    default_path = StringCol()
    
    config = ForeignKey('Config')
    archs = RelatedJoin('Arch')
    mirror_releases = MultipleJoin('MirrorRelease')

class Arch(SQLObject):
    name = StringCol(alternateID=True)
    comment = StringCol()

    releases = RelatedJoin('Release')
    mirror_archs = MultipleJoin('MirrorArch')

class Protocol(SQLObject):
    name = StringCol(alternateID=True)
    mirrors = RelatedJoin('Mirror')

class Mirror(SQLObject):
    hostname = StringCol(alternateID=True)
    comment = StringCol()

    uptime_percentage = IntCol(default=0)
    minimum_uptime_percentage = IntCol(default=60)

    admin_active = BoolCol(default=False)
    user_active = BoolCol(default=True)
    active = BoolCol(default=False)
    private = BoolCol(default=False)
    
    mirror_releases = MultipleJoin('MirrorRelease')
    protocols = RelatedJoin('Protocol')
    ips = MultipleJoin('IP')
    user = ForeignKey('User')
    
class MirrorRelease(SQLObject):
    release_path = StringCol()

    mirror = ForeignKey('Mirror')
    release = ForeignKey('Release')
    mirror_archs = MultipleJoin('MirrorArch')
    
class MirrorArch(SQLObject):
    is_uptodate = BoolCol(default=False)
    last_failure = DateCol(default=None)
    last_failure_reason = StringCol(default=None)

    arch = ForeignKey('Arch')
    mirror_release = ForeignKey('MirrorRelease')

class IP(SQLObject):
    ip_addr = StringCol(alternateID=True, alternateMethodName="byIPAddr")
    
    mirror = ForeignKey('Mirror')
