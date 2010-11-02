from mirrormanager.model import Location, FileGroup
from sqlobject import SQLObject, BoolCol, IntCol 

# upgrade methodology borrowed from
# http://www.mail-archive.com/sqlobject-discuss@lists.sourceforge.net/msg04714.html

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

def update():
    Location.createTable(ifNotExists=True)
    FileGroup.createTable(ifNotExists=True)

    if 'email_on_drop' not in OldSite.sqlmeta.columns and \
            'email_on_add' not in OldSite.sqlmeta.columns:
        OldSite.addColumn(BoolCol("emailOnDrop", default=False), changeSchema=True)
        OldSite.addColumn(BoolCol("emailOnAdd", default=False), changeSchema=True)
        for s in OldSite.select():
            s.emailOnDrop=False
            s.emailOnAdd=False

    if 'dns_country_host' not in OldHost.sqlmeta.columns:
        OldHost.addColumn(BoolCol("dnsCountryHost", default=False), changeSchema=True)
        for h in OldHost.select():
            h.dnsCountryHost = False

    if 'sortorder' not in OldVersion.sqlmeta.columns and \
            'codename' not in OldVersion.sqlmeta.columns:
        OldVersion.addColumn(IntCol("sortorder", default=0, changeSchema=True)
        OldVersion.addColumn(UnicodeCol("codename", default=None), changeSchema=True)
        for v in OldVersion.select():
            v.sortorder = 0
            v.codename = None
