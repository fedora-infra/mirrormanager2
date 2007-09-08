#!/usr/bin/python
#
# Copyright (c) 2007 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

from SocketServer import StreamRequestHandler, ForkingMixIn, UnixStreamServer, BaseServer
import cPickle as pickle
import os, sys, signal, random, socket
from string import zfill, atoi

from IPy import IP
import GeoIP

socketfile = '/tmp/mirrormanager_mirrorlist_server.sock'

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

def setup_continents():
    global continents
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


def do_countrylist(kwargs, cache, clientCountry, requestedCountries, header):
    hostresults = []
    for c in requestedCountries:
        if cache['byCountry'].has_key(c):
            hostresults.extend(cache['byCountry'][c])
            header += 'country = %s ' % c
    hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)
    
def do_continent(kwargs, cache, clientCountry, header):
    if clientCountry is not None:
        requestedCountries = uniqueify([c.upper() for c in continents[GeoIP.country_continents[clientCountry]] if c != clientCountry ])
        return do_countrylist(kwargs, cache, clientCountry, requestedCountries, header)
    return (header, [])
                
def do_country(kwargs, cache, clientCountry, header):
    if kwargs.has_key('country'):
        requestedCountries = uniqueify([c.upper() for c in kwargs['country'].split(',') ])
        if 'GLOBAL' in requestedCountries:
            return do_global(kwargs, cache, clientCountry, header)
        return do_countrylist(kwargs, cache, clientCountry, requestedCountries, header)
    return (header, [])


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
    if cache['byCountry'].has_key(clientCountry):
        hostresults.extend(cache['byCountry'][clientCountry])
        header += 'country = %s ' % clientCountry
    hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)


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
        repo = kwargs['repo']
        arch = kwargs['arch']
        header = "# repo = %s arch = %s " % (repo, arch)

        try:
            dir = repo_arch_to_directoryname[(repo, arch)]
            cache = mirrorlist_cache[dir]
        except KeyError:
            return [(None, header + 'error: invalid repo or arch')]


    done = 0
    netblock_results = []
    country_results = []
    geoip_results = []
    continent_results = []
    global_results = []
        
    header, netblock_results = do_netblocks(kwargs, cache, header)
    if len(netblock_results) > 0:
        done=1

    client_ip = kwargs['client_ip']
    clientCountry = gi.country_code_by_addr(client_ip)
    
    if not done:
        header, country_results  = do_country(kwargs, cache, clientCountry, header)
        if len(country_results) > 0:
            done = 1

    if not done:
        header, geoip_results    = do_geoip(kwargs, cache, clientCountry, header)
        if len(geoip_results) >= 3:
            done = 1

    if not done:
        header, continent_results = do_continent(kwargs, cache, clientCountry, header)
        if len(geoip_results) + len(continent_results) >= 3:
            done = 1

    if not done:
        header, global_results = do_global(kwargs, cache, clientCountry, header)

    random.shuffle(netblock_results)
    random.shuffle(country_results)
    random.shuffle(geoip_results)
    random.shuffle(continent_results)
    random.shuffle(global_results)
    
    hostresults = uniqueify(netblock_results + country_results + geoip_results + continent_results + global_results)
    message = [(None, header)]
    return append_filename_to_results(file, message + hostresults)


def read_caches():
    global mirrorlist_cache
    global host_netblock_cache
    global host_country_allowed_cache
    global repo_arch_to_directoryname

    data = {}
    try:
        f = open('/tmp/mirrorlist_cache.pkl', 'r')
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

            results = do_mirrorlist(d)
            del d
            del p

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
    signal.signal(signal.SIGHUP, sighup_handler)

class ForkingUnixStreamServer(ForkingMixIn, UnixStreamServer):
    def finish_request(self, request, client_address):
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        BaseServer.finish_request(self, request, client_address)


def main():
    try:
        os.unlink(socketfile)
    except:
        pass

    global gi
    gi = GeoIP.new(GeoIP.GEOIP_STANDARD)
    read_caches()
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
