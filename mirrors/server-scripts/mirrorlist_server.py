#!/usr/bin/python
#
# Copyright (c) 2007 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

from SocketServer import StreamRequestHandler, ForkingMixIn, UnixStreamServer, BaseServer
import cPickle as pickle
import os, sys, signal, random, socket, getopt
from string import zfill, atoi

from IPy import IP
import GeoIP

# can be overridden on the command line
socketfile = '/tmp/mirrormanager_mirrorlist_server.sock'
repo_redirect_file = 'repo_redirect.txt'
country_continent_redirect_file = 'country_continent_redirect.txt'
cachefile = '/tmp/mirrorlist_cache.pkl'
# at a point in time when we're no longer serving content for versions
# that don't use yum prioritymethod=fallback
# (e.g. after Fedora 7 is past end-of-life)
# then we can set this value to True
# this only affects results requested using path=...
# for dirs which aren't repositories (such as iso/)
# because we don't know the Version associated with that dir here.
default_ordered_mirrorlist = False

gi = None

# key is strings in tuple (repo.prefix, arch)
mirrorlist_cache = {}

# key is directory.name, returns keys for mirrorlist_cache
directory_name_to_mirrorlist = {}

# key is an IPy.IP structure, value is list of host ids
host_netblock_cache = {}

# key is hostid, value is list of countries to allow
host_country_allowed_cache = {}

repo_arch_to_directoryname = {}

# redirect from a repo with one name to a repo with another
repo_redirect = {}

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


def append_filename_to_results(file, results):
    if file is None:
        return results
    newresults = []
    for country, hcurl in results:
        if country is not None:
            hcurl = hcurl + '/%s' % (file)
        newresults.append((country, hcurl))
    return newresults

continents = {}

def read_country_continent_redirect():
    data = {}
    try:
        f = open(country_continent_redirect_file, 'r')
    except:
        return

    for line in f.readlines():
        if line.startswith('#') or len(line.strip()) == 0:
            continue
        sline = line.split('=')
        try:
            data[sline[0].strip().upper()] = sline[1].strip().upper()
        except:
            pass

    f.close()
    for country, continent in data.iteritems():
        GeoIP.country_continents[country] = continent
        

def setup_continents():
    global continents
    read_country_continent_redirect()
    for c in GeoIP.country_continents.keys():
        continent = GeoIP.country_continents[c]
        if continent not in continents:
            continents[continent] = [c]
        else:
            continents[continent].append(c)
    

def do_global(kwargs, cache, clientCountry, header):
    hostresults = trim_by_client_country(cache['global'], clientCountry)
    header += 'country = global '
    return (header, hostresults)

def do_countrylist(kwargs, cache, clientCountry, requested_countries, header):
    hostresults = []
    for c in requested_countries:
        if cache['byCountry'].has_key(c):
            hostresults.extend(cache['byCountry'][c])
            header += 'country = %s ' % c
    hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)

def get_same_continent_countries(clientCountry, requested_countries):
    result = []
    for r in requested_countries:
        if r is not None:
            requestedCountries = [c.upper() for c in continents[GeoIP.country_continents[r]] \
                                      if c != clientCountry ]
            result.extend(requestedCountries)
    uniqueify(result)
    return result
    
def do_continent(kwargs, cache, clientCountry, requested_countries, header):
    if len(requested_countries) > 0:
        rc = requested_countries
    else:
        rc = [clientCountry]
    clist = get_same_continent_countries(clientCountry, rc)
    return do_countrylist(kwargs, cache, clientCountry, clist, header)
                
def do_country(kwargs, cache, clientCountry, requested_countries, header):
    if 'GLOBAL' in requested_countries:
        return do_global(kwargs, cache, clientCountry, header)
    return do_countrylist(kwargs, cache, clientCountry, requested_countries, header)

def do_netblocks(kwargs, cache, header):
    client_ip = kwargs['client_ip']    
    if not kwargs.has_key('netblock') or kwargs['netblock'] == "1":
        hosts = client_netblocks(client_ip)
        if len(hosts) > 0:
            hostresults = []
            for hostId in hosts:
                if cache['byHostId'].has_key(hostId):
                    hostresults.extend(cache['byHostId'][hostId])
                    header += 'Using preferred netblock'
            if len(hostresults) > 0:
                return (header, hostresults)
    return (header, [])
                
def do_geoip(kwargs, cache, clientCountry, header):
    hostresults = []
    if clientCountry is not None and cache['byCountry'].has_key(clientCountry):
        hostresults.extend(cache['byCountry'][clientCountry])
        header += 'country = %s ' % clientCountry
    hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)

def append_path(hostresults, cache):
    results = []
    if 'subpath' in cache:
        path = cache['subpath']
        for (hostid, hcurl) in hostresults:
            results.append((hostid, "%s/%s" % (hcurl, path)))
    else:
        results = hostresults
    return results


def do_mirrorlist(kwargs):
    if not (kwargs.has_key('repo') and kwargs.has_key('arch')) and not kwargs.has_key('path'):
        return [(None, '# either path=, or repo= and arch= must be specified')]

    file = None
    cache = None
    if kwargs.has_key('path'):
        path = kwargs['path'].strip('/')
        header = "# path = %s " % (path)

        sdir = path.split('/')
        try:
            # path was to a directory
            cache = mirrorlist_cache['/'.join(sdir)]
        except KeyError:
            # path was to a file, try its directory
            file = sdir[-1]
            sdir = sdir[:-1]
            try:
                cache = mirrorlist_cache['/'.join(sdir)]
            except KeyError:
                return [(None, header + 'error: invalid path')]
        
    else:
        if u'source' in kwargs['repo']:
            kwargs['arch'] = u'source'
        repo = repo_redirect.get(kwargs['repo'], kwargs['repo'])
        arch = kwargs['arch']
        header = "# repo = %s arch = %s " % (repo, arch)

        try:
            dir = repo_arch_to_directoryname[(repo, arch)]
            cache = mirrorlist_cache[dir]
        except KeyError:
            return [(None, header + 'error: invalid repo or arch')]


    ordered_mirrorlist = cache.get('ordered_mirrorlist', default_ordered_mirrorlist)
    done = 0
    netblock_results = []
    country_results = []
    geoip_results = []
    continent_results = []
    global_results = []

    requested_countries = []
    if kwargs.has_key('country'):
        requested_countries = uniqueify([c.upper() for c in kwargs['country'].split(',') ])
        
    # if they specify a country, don't use netblocks
    if not 'country' in kwargs:
        header, netblock_results = do_netblocks(kwargs, cache, header)
        if len(netblock_results) > 0:
            if not ordered_mirrorlist:
                done=1

    client_ip = kwargs['client_ip']
    clientCountry = gi.country_code_by_addr(client_ip)
    
    if not done and 'country' in kwargs:
        header, country_results  = do_country(kwargs, cache, clientCountry, requested_countries, header)
        if len(country_results) == 0:
            header, continent_results = do_continent(kwargs, cache, clientCountry, requested_countries, header)
        done = 1

    if not done:
        header, geoip_results    = do_geoip(kwargs, cache, clientCountry, header)
        if len(geoip_results) >= 3:
            if not ordered_mirrorlist:
                done = 1

    if not done:
        header, continent_results = do_continent(kwargs, cache, clientCountry, [], header)
        if len(geoip_results) + len(continent_results) >= 3:
            if not ordered_mirrorlist:
                done = 1

    if not done:
        header, global_results = do_global(kwargs, cache, clientCountry, header)

    random.shuffle(netblock_results)
    random.shuffle(country_results)
    random.shuffle(geoip_results)
    random.shuffle(continent_results)
    random.shuffle(global_results)
    
    hostresults = uniqueify(netblock_results + country_results + geoip_results + continent_results + global_results)
    hostresults = append_path(hostresults, cache)
    message = [(None, header)]
    return append_filename_to_results(file, message + hostresults)

def read_repo_redirect():
    global repo_redirect
    data = {}
    try:
        f = open(repo_redirect_file, 'r')
    except:
        return

    for line in f.readlines():
        if line.startswith('#') or len(line.strip()) == 0:
            continue
        sline = line.split('=')
        try:
            data[sline[0].strip()] = sline[1].strip()
        except:
            pass

    f.close()
    if len(data):
        repo_redirect = data

def read_caches():
    global mirrorlist_cache
    global host_netblock_cache
    global host_country_allowed_cache
    global repo_arch_to_directoryname

    data = {}
    try:
        f = open(cachefile, 'r')
        data = pickle.load(f)
        f.close()
    except:
        pass

    if 'mirrorlist_cache' in data:
        mirrorlist_cache = data['mirrorlist_cache']
    if 'host_netblock_cache' in data:
        host_netblock_cache = data['host_netblock_cache']
    if 'host_country_allowed_cache' in data:
        host_country_allowed_cache = data['host_country_allowed_cache']
    if 'repo_arch_to_directoryname' in data:
        repo_arch_to_directoryname = data['repo_arch_to_directoryname']

    del data

class MirrorlistHandler(StreamRequestHandler):
    def handle(self):
        random.seed()
        try:
            # read size of incoming pickle
            readlen = 0
            size = ''
            while readlen < 10:
                size += self.rfile.read(10 - readlen)
                readlen = len(size)
            size = atoi(size)

            # read the pickle
            readlen = 0
            p = ''
            while readlen < size:
                p += self.rfile.read(size - readlen)
                readlen = len(p)
            d = pickle.loads(p)
            self.connection.shutdown(socket.SHUT_RD)
        except:
            pass

        try:
            results = do_mirrorlist(d)
        except:
            results = [(None, '# Server Error')]
        del d
        del p

        try:
            p = pickle.dumps(results)
            self.connection.sendall(zfill('%s' % len(p), 10))
            del results

            self.connection.sendall(p)
            self.connection.shutdown(socket.SHUT_WR)
            del p
        except:
            pass
        

def sighup_handler(signum, frame):
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    if signum == signal.SIGHUP:
        read_caches()
        read_repo_redirect()
    signal.signal(signal.SIGHUP, sighup_handler)

class ForkingUnixStreamServer(ForkingMixIn, UnixStreamServer):
    def finish_request(self, request, client_address):
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        BaseServer.finish_request(self, request, client_address)

def parse_args():
    global cachefile
    global repo_redirect_file
    global country_continent_redirect_file
    global socketfile
    opts, args = getopt.getopt(sys.argv[1:], "c:G:r:s:", ["cache", "continent_redirect", "repo_redirect", "socket"])
    for option, argument in opts:
        if option in ("-c", "--cache"):
            cachefile = argument
        if option in ("-r", "--repo_redirect"):
            repo_redirect_file = argument
        if option in ("-s", "--socket"):
            socketfile = argument
        if option in ("-G", "--continent_redirect"):
            country_continent_redirect_file = argument

def main():
    parse_args()
    oldumask = os.umask(0)
    try:
        os.unlink(socketfile)
    except:
        pass

    global gi
    gi = GeoIP.new(GeoIP.GEOIP_STANDARD)
    read_caches()
    read_repo_redirect()
    setup_continents()
    signal.signal(signal.SIGHUP, sighup_handler)
    ss = ForkingUnixStreamServer(socketfile, MirrorlistHandler)
    ss.request_queue_size = 100
    ss.serve_forever()

    try:
        os.unlink(socketfile)
    except:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
