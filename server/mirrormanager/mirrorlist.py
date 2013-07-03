from mirrormanager.model import Directory, Host, RepositoryRedirect, CountryContinentRedirect, Repository, HostCategoryUrl, Location, Version, Category, NetblockCountry, setup_directory_category_cache
import os
from IPy import IP
import hashlib
import pprint
import dns.resolver
from mirrormanager.lib import append_value_to_cache

global_caches = dict(
    # key is directoryname
    mirrorlist_cache = {},
    # key is strings in tuple (repo.prefix, arch)
    repo_arch_to_directoryname = {},
    # key is an IPy.IP structure, value is list of host ids
    host_netblock_cache = {},
    # key is hostid, value is list of countries to allow
    host_country_allowed_cache = {},
    host_country_cache = {},
    host_bandwidth_cache = {},
    host_asn_cache = {},
    )

def _do_query_directories():
    common_select = 'SELECT directory.id as directory_id, directory.name AS dname, host.id AS hostid, host.country, host_category_url.id, site.private AS siteprivate, host.private AS hostprivate, host.internet2, host.internet2_clients '
    sql1_from = 'FROM directory, host_category_dir, host_category, host_category_url, host, site, category_directory '
    sql2_from = 'FROM directory,                    host_category, host_category_url, host, site, category_directory '
    common_where  = ' WHERE '
    common_where += 'host.site_id = site.id '                                # join criteria
    common_where += 'AND   host_category_url.host_category_id = host_category.id ' # join criteria
    common_where += 'AND   host_category.host_id = host.id '                       # join criteria
    common_where += 'AND   category_directory.directory_id = directory.id '         # join criteria (dir for this category)
    common_where += 'AND   category_directory.category_id = host_category.category_id ' # join criteria
    common_where += 'AND NOT host_category_url.private '
    common_where += 'AND host.user_active AND site.user_active '
    common_where += 'AND host.admin_active AND site.admin_active '
    sql1_clause   = 'AND   host_category_dir.host_category_id = host_category.id ' # join criteria
    sql1_clause  += 'AND   host_category_dir.directory_id = directory.id '       # join criteria
    sql1_clause  += 'AND   host_category_dir.up2date '
    sql2_clause   = 'AND   host_category.always_up2date '

    sql1 = common_select + sql1_from + common_where + sql1_clause
    sql2 = common_select + sql2_from + common_where + sql2_clause
    sql  = 'SELECT * FROM (' + sql1 + ' UNION ' + sql2 + ' ) '
    sql += 'AS subquery '
    sql += 'ORDER BY dname, hostid '

    result = Directory._connection.queryAll(sql)
    return result

def add_host_to_cache(cache, hostid, value):
    append_value_to_cache(cache, hostid, value)


def add_host_to_set(s, hostid):
    s.add(hostid)

def shrink(mc):
    pp = pprint.PrettyPrinter()
    subcaches = ('global', 'byCountry', 'byHostId', 'byCountryInternet2')
    matches = {}
    for d in mc:
        for subcache in subcaches:
            c = mc[d][subcache]
            s = hashlib.sha1(pp.pformat(c)).hexdigest()
            if s in matches:
                mc[d][subcache] = matches[s]
            else:
                matches[s] = c
    return mc

def _do_query_directory_exclusive_host():
    sql  =''
    sql += 'SELECT directory.name AS dname, directory_exclusive_host.host_id '
    sql += 'FROM directory, directory_exclusive_host '
    sql += 'WHERE directory.id = directory_exclusive_host.directory_id '
    sql += 'ORDER BY dname'

    result = Directory._connection.queryAll(sql)
    return result

def query_directory_exclusive_host():
    table = _do_query_directory_exclusive_host()
    cache = {}
    for (dname, hostid) in table:
        if dname not in cache:
            cache[dname] = set([hostid])
        else:
            cache[dname].add(hostid)
    return cache


def populate_directory_cache():
    global global_caches
    result = _do_query_directories()

    directory_exclusive_hosts = query_directory_exclusive_host()
    
    def setup_directory_repo_cache():
        cache = {}
        for r in list(Repository.select()):
            if r.directory:
                cache[r.directory.id] = r
        return cache
    def setup_version_ordered_mirrorlist_cache():
        cache = {}
        for v in list(Version.select()):
            cache[v.id] = v.ordered_mirrorlist
        return cache
    def setup_category_topdir_cache():
        cache = {}
        for c in list(Category.select()):
            cache[c.id] = len(c.topdir.name)+1 # include trailing /
        return cache

    directory_repo_cache = setup_directory_repo_cache()
    directory_category_cache = setup_directory_category_cache()
    version_ordered_mirrorlist_cache = setup_version_ordered_mirrorlist_cache()
    category_topdir_cache = setup_category_topdir_cache()

    cache = {}
    for (directory_id, directoryname, hostid, country, hcurl, siteprivate, hostprivate, i2, i2_clients) in result:
        if directoryname in directory_exclusive_hosts and \
                hostid not in directory_exclusive_hosts[directoryname]:
            continue

        if directoryname not in cache:
            cache[directoryname] = {'global':set(), 'byCountry':{}, 'byHostId':{}, 'ordered_mirrorlist':False, 'byCountryInternet2':{}}

            repo = directory_repo_cache.get(directory_id)

            if repo is not None and repo.arch is not None:
                global_caches['repo_arch_to_directoryname'][(repo.prefix, repo.arch.name)] = directoryname
                cache[directoryname]['ordered_mirrorlist'] = repo.version.ordered_mirrorlist # WARNING - this is a query # fixme use cache

            numcats = len(directory_category_cache.get(directory_id, []))
            if numcats == 0:
                # no category, so we can't know a mirror host's URLs.
                # nothing to add.
                continue
            elif numcats >= 1:
                # any of them will do, so just look at the first one
                category_id = directory_category_cache[directory_id][0]

            # repodata/ directories aren't themselves repositories, their parent dir is
            # we're walking the list in order, so the parent will be added to the cache before the child
            if directoryname.endswith('/repodata'):
                parent = os.path.dirname(directoryname) # parent
                cache[directoryname]['ordered_mirrorlist'] = cache[parent]['ordered_mirrorlist']
        
            cache[directoryname]['subpath'] = directoryname[category_topdir_cache[category_id]:]
            del repo

        if country is not None:
            country = country.upper()

        if not siteprivate and not hostprivate:
            add_host_to_set(cache[directoryname]['global'], hostid)

            if country is not None:
                if country not in cache[directoryname]['byCountry']:
                    cache[directoryname]['byCountry'][country] = set()
                add_host_to_set(cache[directoryname]['byCountry'][country], hostid)

        if country is not None and i2 and ((not siteprivate and not hostprivate) or i2_clients):
            if country not in cache[directoryname]['byCountryInternet2']:
                cache[directoryname]['byCountryInternet2'][country] = set()
            add_host_to_set(cache[directoryname]['byCountryInternet2'][country], hostid)

        add_host_to_cache(cache[directoryname]['byHostId'], hostid, hcurl)

    global_caches['mirrorlist_cache'] = shrink(cache)

def name_to_ips(name):
    result=[]
    recordtypes=('A', 'AAAA')
    for r in recordtypes:
        try:
            records = dns.resolver.query(name, r)
            for rdata in records:
                try:
                    ip = IP(str(rdata))
                    result.append(ip)
                except:
                    continue
        except:
            continue
    return result

def populate_netblock_cache(cache, host):
    if host.is_active() and len(host.netblocks) > 0:
        for n in list(host.netblocks):
            try:
                ip = IP(n.netblock)
                ips = [ip]
            except ValueError:
                # probably a string
                ips = name_to_ips(n.netblock)

            for ip in ips:
                append_value_to_cache(cache, ip, host.id)
    return cache


def populate_host_country_allowed_cache(cache, host):
    if host.is_active() and len(host.countries_allowed) > 0:
        cache[host.id] = [c.country.upper() for c in list(host.countries_allowed)]
    return cache


def populate_host_max_connections_cache(cache, host):
    cache[host.id] = host.max_connections
    return cache

def populate_host_bandwidth_cache(cache, host):
    try:
        i = int(host.bandwidth_int)
        if i < 1: i = 1
        elif i > 100000: i = 100000 # max bandwidth 100Gb
        cache[host.id] = i
    except:
        cache[host.id] = 1

    return cache

def populate_host_country_cache(cache, host):
    cache[host.id] = host.country
    return cache

def populate_host_asn_cache(cache, host):
    if not host.asn_clients: return cache
    if host.asn is not None:
        append_value_to_cache(cache, host.asn, host.id)

    for peer_asn in list(host.peer_asns):
        append_value_to_cache(cache, peer_asn.asn, host.id)
    return cache

def repository_redirect_cache():
    cache = {}
    for r in list(RepositoryRedirect.select()):
        cache[r.fromRepo] = r.toRepo
    return cache

def country_continent_redirect_cache():
    cache = {}
    for c in list(CountryContinentRedirect.select()):
        cache[c.country] = c.continent
    return cache

def disabled_repository_cache():
    cache = {}
    for r in list(Repository.select()):
        if r.disabled:
            cache[r.prefix] = True
    return cache

def file_details_cache():
    # cache{directoryname}{filename}[{details}]
    cache = {}
    # materialize this select to avoid making hundreds of thousands of queries
    for d in list(Directory.select()):
        if len(d.fileDetails) > 0:
            cache[d.name] = {}
            for fd in list(d.fileDetails):
                details = dict(timestamp=fd.timestamp, sha1=fd.sha1, md5=fd.md5, sha256=fd.sha256, sha512=fd.sha512, size=fd.size)
                append_value_to_cache(cache[d.name], fd.filename, details)
    return cache

def hcurl_cache():
    cache = {}
    for hcurl in list(HostCategoryUrl.select()):
        cache[hcurl.id] = hcurl.url
    return cache

def location_cache():
    cache = {}
    for location in list(Location.select()):
        cache[location.name] = [host.id for host in list(location.hosts)]
    return cache

def netblock_country_cache():
    cache = {}
    for n in list(NetblockCountry.select()):
        ip = None
        try:
            ip = IP(n.netblock)
        except:
            continue
        # guaranteed to be unique by database constraints
        cache[ip] = (n.country)
            
    return cache

def populate_host_caches():
    n = dict()
    ca = dict()
    b = dict()
    cc = dict()
    a = dict()
    mc = dict()
    
    for host in list(Host.select()):
        n = populate_netblock_cache(n, host)
        ca = populate_host_country_allowed_cache(ca, host)
        b = populate_host_bandwidth_cache(b, host)
        cc = populate_host_country_cache(cc, host)
        a = populate_host_asn_cache(a, host)
        mc = populate_host_max_connections_cache(mc, host)

    global global_caches
    global_caches['host_netblock_cache'] = n
    global_caches['host_country_allowed_cache'] = ca
    global_caches['host_bandwidth_cache'] = b
    global_caches['host_country_cache'] = cc
    global_caches['host_asn_cache'] = a
    global_caches['host_max_connections_cache'] = mc



def populate_all_caches():
    populate_host_caches()
    populate_directory_cache()

import cPickle as pickle
def dump_caches(filename):
    data = {'mirrorlist_cache':global_caches['mirrorlist_cache'],
            'host_netblock_cache':global_caches['host_netblock_cache'],
            'host_country_allowed_cache':global_caches['host_country_allowed_cache'],
            'host_bandwidth_cache':global_caches['host_bandwidth_cache'],
            'host_country_cache':global_caches['host_country_cache'],
            'host_max_connections_cache':global_caches['host_max_connections_cache'],
            'asn_host_cache':global_caches['host_asn_cache'], # yeah I misnamed this
            'repo_arch_to_directoryname':global_caches['repo_arch_to_directoryname'],
            'repo_redirect_cache':repository_redirect_cache(),
            'country_continent_redirect_cache':country_continent_redirect_cache(),
            'disabled_repositories':disabled_repository_cache(),
            'file_details_cache':file_details_cache(),
            'hcurl_cache':hcurl_cache(),
            'location_cache':location_cache(),
            'netblock_country_cache':netblock_country_cache()}
    
    try:
        f = open(filename, 'w')
        pickle.dump(data, f)
        f.close()
    except:
        pass
