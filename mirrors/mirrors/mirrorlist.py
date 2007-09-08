import cherrypy
import turbogears
from turbogears import controllers, expose, validate, redirect, widgets, validators, error_handler, exception_handler
from sqlobject import *
from sqlobject.sqlbuilder import *
from mirrors.model import *
from IPy import IP

# key is directoryname
mirrorlist_cache = {}

# key is strings in tuple (repo.prefix, arch)
repo_arch_to_directoryname = {}

# key is an IPy.IP structure, value is list of host ids
host_netblock_cache = {}

# key is hostid, value is list of countries to allow
host_country_allowed_cache = {}

def trim(input):
    """ remove all but http and ftp URLs,
    and if both http and ftp are offered,
    leave only http"""
    result = []
    lastdir = None
    for (directoryname, hostid, country, hcurl, siteprivate, hostprivate) in input:
        if lastdir is None or directoryname != lastdir:
            lastdir = directoryname
            l = {}
    
        us = hcurl.split('/')
        uprotocol = us[0]
        umachine = us[2]
        if not l.has_key(hostid):
            l[hostid] = {}
        l[hostid][uprotocol] = (directoryname, hostid, country, hcurl, siteprivate, hostprivate)

        r = []
        for k, v in l.iteritems():
            if v.has_key(u'http:'):
                r.append(v[u'http:'])
            elif v.has_key(u'ftp:'):
                r.append(v[u'ftp:'])
        result.extend(r)

    return result

def _do_query_directories():
    sql  = 'SELECT directory.name, host.id, host.country, host_category_url.url, site.private, host.private '
    sql += 'FROM directory, host_category_dir, host_category, host_category_url, host, site '
    sql += 'WHERE host_category_dir.host_category_id = host_category.id ' # join criteria
    sql += 'AND   host_category_url.host_category_id = host_category.id ' # join criteria
    sql += 'AND   host_category.host_id = host.id '                       # join criteria
    sql += 'AND   host.site_id = site.id '                                # join criteria
    sql += 'AND   host_category_dir.directory_id = directory.id '         # join criteria
    sql += 'AND host_category_dir.up2date '
    sql += 'AND NOT host_category_url.private '
    sql += 'AND host.user_active AND site.user_active '
    sql += 'AND host.admin_active AND site.admin_active '
    sql += 'ORDER BY directory.name '

    result = directory._connection.queryAll(sql)
    return result


def populate_directory_cache():
    result = _do_query_directories()
    result = trim(result)
    
    lastdir = None
    for (directoryname, hostid, country, hcurl, siteprivate, hostprivate) in result:
        if lastdir is None or directoryname != lastdir:
            lastdir = directoryname
            newresult = {'global':[], 'bycountry':{}, 'byhostid':{}}
            d = Directory.byName(directoryname)
            repo = d.repository
        country = country.upper()
        v = (hostid, "%s/%s" % (hcurl, path))
        if not siteprivate and not hostprivate:
            newresult['global'].append(v)

            if not newresult['byCountry'].has_key(country):
                newresult['byCountry'][country] = [v]
            else:
                newresult['byCountry'][country].append(v)

        if not newresult['byHostId'].has_key(hostid):
            newresult['byHostId'][hostid] = [v]
        else:
            newresult['byHostId'][hostid].append(v)

        global mirrorlist_cache
        mirrorlist_cache[directoryname] = newresult
        global repo_arch_to_directoryname
        if repo is not None:
            repo_arch_to_directoryname[(repo.prefix, repo.arch.name)] = directory.name
    

def populate_netblock_cache():
    cache = {}
    for host in Host.select():
        if host.is_active() and len(host.netblocks) > 0:
            for n in host.netblocks:
                try:
                    ip = IP(n.netblock)
                except:
                    continue
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
    

def populate_all_caches():
    populate_host_country_allowed_cache()
    populate_netblock_cache()
    populate_directory_cache()
    print "mirrorlist caches populated"



import pickle
def dump_caches():
    data = {'mirrorlist_cache':mirrorlist_cache,
            'host_netblock_cache':host_netblock_cache,
            'host_country_allowed_cache':host_country_allowed_cache,
            'repo_arch_to_directoryname':repo_arch_to_directoryname}
    
    try:
        f = open('/tmp/mirrorlist_cache.pkl', 'w')
        pickle.dump(data, f)
        f.close()
    except:
        pass
