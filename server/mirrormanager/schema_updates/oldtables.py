from sqlobject import *

from turbogears.database import PackageHub
hub = PackageHub("mirrormanager")
__connection__ = hub

# upgrade methodology borrowed from
# http://www.mail-archive.com/sqlobject-discuss@lists.sourceforge.net/msg04714.html

class OldSiteToSite(SQLObject):
    class sqlmeta:
        fromDatabase = True
        table = 'site_to_site'

class OldSite(SQLObject):
    class sqlmeta:
        fromDatabase = True
        table = 'site'

class OldHost(SQLObject):
    class sqlmeta:
        fromDatabase = True
        table = 'host'

class OldVersion(SQLObject):
    class sqlmeta:
        fromDatabase = True
        table = 'version'

class OldProduct(SQLObject):
    class sqlmeta:
        fromDatabase = True
        table = 'product'

class OldCategory(SQLObject):
    class sqlmeta:
        fromDatabase = True
        table = 'category'

class OldHostNetblock(SQLObject):
    class sqlmeta:
        fromDatabase = True
        table = 'host_netblock'

class OldHostCategory(SQLObject):
    class sqlmeta:
        fromDatabase = True
        table = 'host_category'
