from sqlobject import *
from sqlobject.sqlbuilder import *
from turbogears import identity, config
from mirrormanager.model import *
from sqlobject import SQLObject, BoolCol, IntCol 
from oldtables import *

from turbogears.database import PackageHub
hub = PackageHub("mirrormanager")
__connection__ = hub

changes = {}

def change_tables():
    global changes

    Location.createTable(ifNotExists=True)
    FileGroup.createTable(ifNotExists=True)
    HostLocation.createTable(ifNotExists=True)
    Country.createTable(ifNotExists=True)
    HostCountry.createTable(ifNotExists=True)

    if 'emailOnDrop' not in OldSite.sqlmeta.columns and \
            'emailOnAdd' not in OldSite.sqlmeta.columns:
        OldSite.sqlmeta.addColumn(BoolCol("emailOnDrop", default=False), changeSchema=True)
        OldSite.sqlmeta.addColumn(BoolCol("emailOnAdd", default=False), changeSchema=True)
        changes['site.email_on_drop_add'] = True
        
    # Host
    # ensure this isn't present anymore
    if 'dnsCountryHost' in OldHost.sqlmeta.columns:
        OldHost.sqlmeta.delColumn("dnsCountryHost"), changeSchema=True)

    if 'sortorder' not in OldVersion.sqlmeta.columns and \
            'codename' not in OldVersion.sqlmeta.columns:
        OldVersion.sqlmeta.addColumn(IntCol("sortorder", default=0), changeSchema=True)
        OldVersion.sqlmeta.addColumn(UnicodeCol("codename", default=None), changeSchema=True)
        changes['version.sortorder_codename'] = True

    if 'publiclist' not in OldProduct.sqlmeta.columns:
        OldProduct.sqlmeta.addColumn(BoolCol("publiclist", default=True), changeSchema=True)
        changes['product.publiclist'] = True

    if 'geoDnsDomain' not in OldCategory.sqlmeta.columns:
        OldCategory.sqlmeta.addColumn(UnicodeCol("GeoDNSDomain", default=None), changeSchema=True)
        changes['category.geo_dns_domain'] = True

def fill_new_columns():
    global changes

    if changes.get('site.email_on_drop_add'):
        for s in Site.select():
            s.emailOnDrop=False
            s.emailOnAdd=False

    if changes.get('version.sortorder_codename'):
        for v in Version.select():
            v.sortorder = 0
            v.codename = None

    if changes.get('product.publiclist'):
        for p in Product.select():
            p.publiclist = True

    if changes.get('category.geo_dns_domain'):
        for c in Category.select():
            c.GeoDNSDomain = None




def update():
    """Fills newly created database columns with information.
    Run this after using tg-admin sql upgrade.
    """
    change_tables()
    fill_new_columns()
