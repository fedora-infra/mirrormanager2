from mirrormanager.model import Directory, Host, RepositoryRedirect, CountryContinentRedirect, Repository, HostCategoryUrl, Location
from IPy import IP
import os
import sha
import pprint
import dns.resolver

# key is directoryname
mirrorlist_cache = {}

# key is strings in tuple (repo.prefix, arch)
repo_arch_to_directoryname = {}

# key is an IPy.IP structure, value is list of host ids
host_netblock_cache = {}

# key is hostid, value is list of countries to allow
host_country_allowed_cache = {}

def _do_query_directories():
    common_select = 'SELECT directory.name AS dname, host.id AS hostid, host.country, host_category_url.id, site.private AS siteprivate, host.private AS hostprivate, host.internet2, host.internet2_clients '
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

def add_host_to_cache(cache, hostid, hcurl):
    if hostid not in cache:
        cache[hostid] = [hcurl]
    else:
        cache[hostid].append(hcurl)
    return cache

def add_host_to_set(s, hostid):
    s.add(hostid)

def shrink(mc):
    pp = pprint.PrettyPrinter()
    subcaches = ('global', 'byCountry', 'byHostId', 'byCountryInternet2')
    matches = {}
    for d in mc:
        for subcache in subcaches:
            c = mc[d][subcache]
            s = sha.sha(pp.pformat(c))
            if s in matches:
                d[c] = matches[s]
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
    global repo_arch_to_directoryname
    result = _do_query_directories()

    directory_exclusive_hosts = query_directory_exclusive_host()

    directory_exclusive_hosts = query_directory_exclusive_host()

    cache = {}
    for (directoryname, hostid, country, hcurl, siteprivate, hostprivate, i2, i2_clients) in result:
        if directoryname in directory_exclusive_hosts and \
                hostid not in directory_exclusive_hosts[directoryname]:
            continue

        if directoryname not in cache:
            cache[directoryname] = {'global':set(), 'byCountry':{}, 'byHostId':{}, 'ordered_mirrorlist':False, 'byCountryInternet2':{}}
            directory = Directory.byName(directoryname)
            repo = directory.repository
            # if a directory is in more than one category, problem...
            if repo is not None and repo.arch is not None:
                repo_arch_to_directoryname[(repo.prefix, repo.arch.name)] = directory.name
                category = repo.category
                cache[directoryname]['ordered_mirrorlist'] = repo.version.ordered_mirrorlist
            else:
                numcats = len(directory.categories)
                if numcats == 0:
                    # no category, so we can't know a mirror host's URLs.
                    # nothing to add.
                    continue
                elif numcats >= 1:
                    # any of them will do, so just look at the first one
                    category = directory.categories[0]

                # repodata/ directories aren't themselves repositories, their parent dir is
                # we're walking the list in order, so the parent will be added to the cache before the child
                if directoryname.endswith('/repodata'):
                    parent = os.path.dirname(directoryname) # parent
                    cache[directoryname]['ordered_mirrorlist'] = cache[parent]['ordered_mirrorlist']
        
            cache[directoryname]['subpath'] = directoryname[len(category.topdir.name)+1:]
            del repo
            del directory
            del category

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

    global mirrorlist_cache
    mirrorlist_cache = shrink(cache)

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

def populate_netblock_cache():
    cache = {}
    for host in Host.select():
        if host.is_active() and len(host.netblocks) > 0:
            for n in host.netblocks:
                try:
                    ip = IP(n.netblock)
                    ips = [ip]
                except ValueError:
                    # probably a string
                    ips = name_to_ips(n.netblock)

                for ip in ips:
                    if cache.has_key(ip):
                        cache[ip].append(host.id)
                    else:
                        cache[ip] = [host.id]

    global host_netblock_cache
    host_netblock_cache = cache

def populate_host_country_allowed_cache():
    cache = {}
    for host in Host.select():
        if host.is_active() and len(host.countries_allowed) > 0:
            cache[host.id] = [c.country.upper() for c in host.countries_allowed]
    global host_country_allowed_cache
    host_country_allowed_cache = cache

def host_bandwidth_cache():
    cache = {}
    for host in Host.select():
        cache[host.id] = host.bandwidth_int
    return cache

def host_country_cache():
    cache = {}
    for host in Host.select():
        cache[host.id] = host.country
    return cache

def asn_host_cache():
    cache = {}
    for host in Host.selectBy(asn_clients=True):
        if host.asn is not None:
            if host.asn not in cache:
                cache[host.asn] = [host.id]
            else:
                cache[host.asn].append[host.id]

        for peer_asn in host.peer_asns:
            if peer_asn.asn not in cache:
                cache[peer_asn.asn] = [host.id]
            else:
                cache[peer_asn.asn].append(host.id)
    return cache

def repository_redirect_cache():
    cache = {}
    for r in RepositoryRedirect.select():
        cache[r.fromRepo] = r.toRepo
    return cache

def country_continent_redirect_cache():
    cache = {}
    for c in CountryContinentRedirect.select():
        cache[c.country] = c.continent
    return cache

def disabled_repository_cache():
    cache = {}
    for r in Repository.select():
        if r.disabled:
            cache[r.prefix] = True
    return cache

def file_details_cache():
    # cache{directoryname}{filename}[{details}]
    cache = {}
    for d in Directory.select():
        if len(d.fileDetails) > 0:
            cache[d.name] = {}
            for fd in d.fileDetails:
                details = dict(timestamp=fd.timestamp, sha1=fd.sha1, md5=fd.md5, sha256=fd.sha256, sha512=fd.sha512, size=fd.size)
                if fd.filename not in cache[d.name]:
                    cache[d.name][fd.filename] = [details]
                else:
                    cache[d.name][fd.filename].append(details)
    return cache

def hcurl_cache():
    cache = {}
    for hcurl in HostCategoryUrl.select():
        cache[hcurl.id] = hcurl.url
    return cache

def location_cache():
    cache = {}
    for location in Location.select():
        cache[location.name] = [host.id for host in location.hosts]
    return cache

def netblock_country_cache():
    cache = {}
    for n in NetblockCountry.select():
        ip = None
        try:
            ip = IP(n.netblock)
        except:
            continue
        # guaranteed to be unique by database constraints
        cache[ip.strNormal()] = (n.country)
            
    return cache


def populate_all_caches():
    populate_host_country_allowed_cache()
    populate_netblock_cache()
    populate_directory_cache()

import cPickle as pickle
def dump_caches():
    data = {'mirrorlist_cache':mirrorlist_cache,
            'host_netblock_cache':host_netblock_cache,
            'host_country_allowed_cache':host_country_allowed_cache,
            'repo_arch_to_directoryname':repo_arch_to_directoryname,
            'repo_redirect_cache':repository_redirect_cache(),
            'country_continent_redirect_cache':country_continent_redirect_cache(),
            'disabled_repositories':disabled_repository_cache(),
            'host_bandwidth_cache':host_bandwidth_cache(),
            'host_country_cache':host_country_cache(),
            'file_details_cache':file_details_cache(),
            'hcurl_cache':hcurl_cache(),
            'asn_host_cache':asn_host_cache(),
            'location_cache':location_cache(),
            'netblock_country_cache':netblock_country_cache()}
    
    try:
        f = open('/var/lib/mirrormanager/mirrorlist_cache.pkl', 'w')
        pickle.dump(data, f)
        f.close()
    except:
        pass
