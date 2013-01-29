from sqlobject import *
from sqlobject.sqlbuilder import *
from turbogears import identity, config
from mirrormanager.model import *
from sqlobject import SQLObject, BoolCol, IntCol, UnicodeCol
from sqlobject.index import SODatabaseIndex
from oldtables import *
import GeoIP
import inspect

from turbogears.database import PackageHub
hub = PackageHub("mirrormanager")
__connection__ = hub

changes = {}

# On Postgres at least, one cannot create a new column with notNull=True, even with default=<something>
# because it will fail to create the column, claiming the new column is full of null values,
# which violates the notNull constraint.
# So, you have to create the column, fill it with the default value, and then
# add the notNull=True constraint thereafter.

def _set_not_null(table, col):
    _dburi = config.get('sqlobject.dburi', '')
    if 'mysql://' in _dburi:
        sql = 'ALTER TABLE %s CHANGE COLUMN %s BIGINT NOT NULL' % (table.sqlmeta.table, col)
    elif 'postgres://' in _dburi:
        sql = 'ALTER TABLE %s ALTER COLUMN %s SET NOT NULL' % (table.sqlmeta.table, col)
    return table._connection.query(sql)

def bandwidth_int_not_null():
    for h in OldHost.select():
        if h.bandwidthInt is None: # note column name differs due to underscore->CamelCase conversion
            h.bandwidthInt = 100
    _set_not_null(OldHost, 'bandwidth_int')

def _SODatabaseIndex_needs_creationOrder():
    argspec = inspect.getargspec(SODatabaseIndex.__init__)
    return 'creationOrder' in argspec.args

def change_tables():
    global changes

    Location.createTable(ifNotExists=True)
    FileGroup.createTable(ifNotExists=True)
    FileDetailFileGroup.createTable(ifNotExists=True)
    HostLocation.createTable(ifNotExists=True)
    Country.createTable(ifNotExists=True)
    HostCountry.createTable(ifNotExists=True)
    NetblockCountry.createTable(ifNotExists=True)
    HostPeerAsn.createTable(ifNotExists=True)

    if 'emailOnDrop' not in OldSite.sqlmeta.columns and \
            'emailOnAdd' not in OldSite.sqlmeta.columns:
        OldSite.sqlmeta.addColumn(BoolCol("emailOnDrop", default=False), changeSchema=True)
        OldSite.sqlmeta.addColumn(BoolCol("emailOnAdd", default=False), changeSchema=True)
        changes['site.email_on_drop_add'] = True
        
    # Host
    # ensure this isn't present anymore
    if 'dnsCountryHost' in OldHost.sqlmeta.columns:
        OldHost.sqlmeta.delColumn("dnsCountryHost", changeSchema=True)

    if 'maxConnections' not in OldHost.sqlmeta.columns:
        OldHost.sqlmeta.addColumn(IntCol("max_connections", default=1), changeSchema=True)
        changes['host.max_connections'] = True

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


    def _add_site_to_site_index():
        if _SODatabaseIndex_needs_creationOrder():
            idx = SODatabaseIndex(OldSiteToSite, 'username_idx',
                                  [dict(column='upstream_site_id'),
                                   dict(column='username', length=UnicodeColKeyLength)],
                                  0, unique=True)
        else:
            idx = SODatabaseIndex(OldSiteToSite, 'username_idx',
                                  [dict(column='upstream_site_id'),
                                   dict(column='username', length=UnicodeColKeyLength)],
                                  unique=True)
            
        sql = SiteToSite._connection.createIndexSQL(SiteToSite, idx)
        try:
            OldSiteToSite._connection.queryAll(sql)
        except: # already exists
            pass


    if 'username' not in OldSiteToSite.sqlmeta.columns and \
            'password' not in OldSiteToSite.sqlmeta.columns:
        OldSiteToSite.sqlmeta.addColumn(UnicodeCol("username", default=None), changeSchema=True)
        OldSiteToSite.sqlmeta.addColumn(UnicodeCol("password", default=None), changeSchema=True)
        _add_site_to_site_index()
        changes['sitetosite.username_password'] = True

    if 'name' not in OldHostNetblock.sqlmeta.columns:
        OldHostNetblock.sqlmeta.addColumn(UnicodeCol("name", default=None), changeSchema=True)
        changes['hostnetblock.name'] = True

    def _add_version_index():
        _dburi = config.get('sqlobject.dburi', '')
        if 'mysql://' in _dburi and OldVersion.sqlmeta.columns['name'].length != UnicodeColKeyLength:
            sql = 'ALTER TABLE %s CHANGE COLUMN name name VARCHAR(%s)' % (OldVersion.sqlmeta.table, UnicodeColKeyLength)
            OldVersion._connection.queryAll(sql)

        if _SODatabaseIndex_needs_creationOrder():
            idx = SODatabaseIndex(OldVersion, 'idx',
                                  [dict(column='name', length=UnicodeColKeyLength),
                                   dict(column='productID')],
                                  0, unique=True)
        else:
            idx = SODatabaseIndex(OldVersion, 'idx',
                                  [dict(column='name', length=UnicodeColKeyLength),
                                   dict(column='productID')],
                                  unique=True)
            
        sql = Version._connection.createIndexSQL(Version, idx)
        try:
            result = OldVersion._connection.queryAll(sql)
        except: # it already exists
            pass

    _add_version_index()
    bandwidth_int_not_null()

    # delete unused HostCategory fields
    for c in ('adminActive', 'userActive', 'upstream'): 
        if c in OldHostCategory.sqlmeta.columns:
            OldHostCategory.sqlmeta.delColumn(c, changeSchema=True)

    # delete unused Host fields
    for c in ('bandwidth'):
        if c in OldHost.sqlmeta.columns:
            OldHost.sqlmeta.delColumn(c, changeSchema=True)

    # delete unused Directory fields
    for c in ('versionIDID', 'archIDID'):
        if c in OldDirectory.sqlmeta.columns:
            OldDirectory.sqlmeta.delColumn(c, changeSchema=True)

    # delete unused HostCategoryDir fields
    for c in ('lastCrawled', 'files'):
        if c in OldHostCategoryDir.sqlmeta.columns:
            OldHostCategoryDir.sqlmeta.delColumn(c, changeSchema=True)


def update_countries():
    db_countries = set(c.code for c in Country.select())
    geoip_countries = set(GeoIP.country_codes)
    diff =  geoip_countries.difference(db_countries)
    for cc in diff:
        Country(code=cc)

def fill_new_columns():
    global changes

    if changes.get('site.email_on_drop_add'):
        for s in Site.select():
            s.emailOnDrop=False
            s.emailOnAdd=False

    if changes.get('host.max_connections'):
        for h in Host.select():
            h.max_connections = 1
            _set_not_null(OldHost, 'max_connections')
            

    if changes.get('version.sortorder_codename'):
        for v in Version.select():
            v.sortorder = 0
            v.codename = None
        _set_not_null(OldVersion, 'sortorder')

    if changes.get('product.publiclist'):
        for p in Product.select():
            p.publiclist = True

    if changes.get('category.geo_dns_domain'):
        for c in Category.select():
            c.GeoDNSDomain = None

    if changes.get('sitetosite.username_password'):
        for s in SiteToSite.select():
            s.username = None
            s.password = None

    if changes.get('hostnetblock.name'):
        for n in HostNetblock.select():
            n.name = None

    update_countries()


def update():
    change_tables()
    fill_new_columns()
