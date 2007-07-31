from IPy import IP
import GeoIP
from mod_python import util
from mod_python import apache
import pickle
from datetime import datetime, timedelta

gi = GeoIP.new(GeoIP.GEOIP_STANDARD)

# key is strings in tuple (repo.prefix, arch)
mirrorlist_cache = {}

# key is an IPy.IP structure, value is list of host ids
host_netblock_cache = {}

# key is hostid, value is list of countries to allow
host_country_allowed_cache = {}



def uniqueify(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


def get_repo_cache(*args, **kwargs):
    if not kwargs.has_key('repo') or not kwargs.has_key('arch'):
        return
    repo = kwargs['repo']

    if u'source' in kwargs['repo']:
        kwargs['arch'] = u'source'

    if mirrorlist_cache.has_key((repo, arch)):
        return mirrorlist_cache[(repo, arch)]
    else:
        raise KeyError


def client_netblocks(ip):
    result = []
    try:
        clientIP = IP(ip)
    except:
        return result
    for k,v in host_netblock_cache.iteritems():
        if clientIP in k:
            result.extend(v)
    return result

def client_in_host_allowed(clientCountry, hostID):
    if host_country_allowed.has_key(hostID):
        if clientCountry.upper() in host_country_allowed[hostID]:
            return True
        return False
    return True



def trim_by_client_country(hostresults, clientCountry):
    if clientCountry is None:
        return hostresults

    results = []

    for hostid, hcurl in hostresults:
        if not host_country_allowed_cache.has_key(hostid):
            results.append((hostid, hcurl))
        else:
            if clientCountry in host_country_allowed_cache[hostid]:
                results.append((hostid, hcurl))

    return results


def real_client_ip(xforwardedfor):
    """Only the last-most entry listed is the where the client
    connection to us came from, so that's the only one we can trust in
    any way."""
    return xforwardedfor.split(',')[-1].strip()

def mirrorlist_magic(req, *args, **kwargs):
    if not kwargs.has_key('repo') or not kwargs.has_key('arch'):
        return [(None, '# either repo= or arch= not speficied')]

    if u'source' in kwargs['repo']:
        kwargs['arch'] = u'source'
    repo = kwargs['repo']
    arch = kwargs['arch']

    header = "# repo = %s arch = %s " % (repo, arch)
    if not mirrorlist_cache.has_key((repo, arch)):
        return [(None, header + 'error: invalid repo or arch')]
    cache = mirrorlist_cache[(repo, arch)]

    client_ip = req.get_remote_host()
    if kwargs.has_key('ip'):
        client_ip = kwargs['ip']
    else:
        if req.headers_in.has_key('X-Forwarded-For'):
            client_ip = real_client_ip(req.headers_in['X-Forwarded-For'])
            
    clientCountry = gi.country_code_by_addr(client_ip)

    # handle netblocks
    if not kwargs.has_key('country'):
        hosts = client_netblocks(client_ip)
        if len(hosts) > 0:
            hostresults = []
            for hostId in hosts:
                if cache['byHostId'].has_key(hostId):
                    hostresults.extend(cache['byHostId'][hostId])
                    header += 'Using preferred netblock'
            if len(hostresults) > 0:
                message = [(None, header)]
                return message + hostresults

    # handle country request lists
    if kwargs.has_key('country'):
        requestedCountries = uniqueify([c.upper() for c in kwargs['country'].split(',') ])
        if 'GLOBAL' in requestedCountries:
            hostresults = trim_by_client_country(cache['global'], clientCountry)
            header += 'country = global'
            message = [(None, header)]
            return message + hostresults

        hostresults = []
        for c in requestedCountries:
            if cache['byCountry'].has_key(c):
                hostresults.extend(cache['byCountry'][c])
                header += 'country = %s' % c
        hostresults = trim_by_client_country(hostresults, clientCountry)

        # if not enough per-country mirrors, return the global list
        if len(hostresults) < 3:
            hostresults = trim_by_client_country(cache['global'], clientCountry)
            header += ' country = global'
            message = [(None, header)]
            return message + hostresults

        
        message = [(None, header)]
        return message + hostresults

    # fall back to GeoIP-based lookups
    hostresults = []
    if cache['byCountry'].has_key(clientCountry):
        hostresults.extend(cache['byCountry'][clientCountry])
        header += 'country = %s ' % clientCountry
    hostresults = trim_by_client_country(hostresults, clientCountry)

    # if not enough per-country mirrors, return the global list
    # fixme should maybe return lists from countries on same continent
    if len(hostresults) < 3:
        hostresults = trim_by_client_country(cache['global'], clientCountry)
        header += 'country = global '
        message = [(None, header)]
        return message + hostresults

    header += ' country = %s' % clientCountry
    message = [(None, header)]
    return message + hostresults

def do_mirrorlist(req, *args, **kwargs):
    results = mirrorlist_magic(req, *args, **kwargs)
    results =  [url for hostid, url in results]
    return results

def read_caches():
    data = {'mirrorlist_cache':mirrorlist_cache,
            'host_netblock_cache':host_netblock_cache,
            'host_country_allowed_cache':host_country_allowed_cache}
    
    f = open('/tmp/mirrorlist_cache.pkl', 'r')
    p = f.read()
    data = pickle.loads(p)
    f.close()

    global mirrorlist_cache
    global host_netblock_cache
    global host_country_allowed_cache

    if 'mirrorlist_cache' in data:
        mirrorlist_cache = data['mirrorlist_cache']
    if 'host_netblock_cache' in data:
        host_netblock_cache = data['host_netblock_cache']
    if 'host_country_allowed_cache' in data:
        host_country_allowed_cache = data['host_country_allowed_cache']




next = None

def handler(req):
    global next
    now = datetime.utcnow()
    if next is None or now > next:
        read_caches()
        next = now + timedelta(hours=1)
        
    request_data = util.FieldStorage(req)
    fields = ['repo', 'arch', 'country', 'ip']        
    d = {}
    for f in fields:
        if f in request_data:
            d[f] = request_data[f]
    
    results = do_mirrorlist(req, **d)
    req.content_type = "text/plain"
    result = ""
    for line in results:
        result += line + '\n'
        
    req.write(result)
    return apache.OK

