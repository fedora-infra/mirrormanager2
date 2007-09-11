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
    l = {}
    for hostid, country, hcurl, siteprivate, hostprivate in input:
        us = hcurl.split('/')
        uprotocol = us[0]
        umachine = us[2]
        if not l.has_key(hostid):
            l[hostid] = {}
        l[hostid][uprotocol] = (hostid, country, hcurl, siteprivate, hostprivate)

    result = []
    for k, v in l.iteritems():
        if v.has_key(u'http:'):
            result.append(v[u'http:'])
        elif v.has_key(u'ftp:'):
            result.append(v[u'ftp:'])

    return result

def _do_query_directory(directory, category):
    sql  = 'SELECT host.id, host.country, host_category_url.url, site.private, host.private '
    sql += 'FROM host_category_dir, host_category, host_category_url, host, site '
    sql += 'WHERE host_category_dir.host_category_id = host_category.id ' # join criteria
    sql += 'AND   host_category_url.host_category_id = host_category.id ' # join criteria
    sql += 'AND   host_category.host_id = host.id '                       # join criteria
    sql += 'AND   host.site_id = site.id '                                # join criteria
    sql += 'AND host_category.category_id = %d ' % category.id # but select only the target category
    sql += "AND host_category_dir.directory_id = %s " % directory.id # and target directory
    sql += 'AND (host_category_dir.up2date OR host_category.always_up2date) '
    sql += 'AND NOT host_category_url.private '
    sql += 'AND host.user_active AND site.user_active '
    sql += 'AND host.admin_active AND site.admin_active '

    result = directory._connection.queryAll(sql)
    result = trim(result)
    return result

def populate_directory_cache(directory):
    repo = directory.repository
    # if a directory is in more than one category, problem...
    if repo is not None:
        category = repo.category
    else:
        numcats = len(directory.categories)
        if numcats == 0:
            # no category, so we can't know a mirror host's URLs.
            # nothing to add.
            return
        elif numcats >= 1:
            # any of them will do, so just look at the first one
            category = directory.categories[0]
        
    path = directory.name[len(category.topdir.name)+1:]
    result = _do_query_directory(directory, category)
    
    newresult = {'global':[], 'byCountry':{}, 'byHostId':{}, 'subpath':path}
    for (hostid, country, hcurl, siteprivate, hostprivate) in result:
        country = country.upper()
        v = (hostid, hcurl)
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
    mirrorlist_cache[directory.name] = newresult
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
    for d in Directory.select():
        populate_directory_cache(d)
    print "mirrorlist caches populated"



import cPickle as pickle
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
