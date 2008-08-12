#!/usr/bin/python
#
# Copyright (c) 2007 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

from SocketServer import StreamRequestHandler, ForkingMixIn, UnixStreamServer, BaseServer
import cPickle as pickle
import os, sys, signal, random, socket, getopt
from string import zfill, atoi
import datetime

from IPy import IP
import GeoIP
import bisect
from weighted_shuffle import weighted_shuffle

# can be overridden on the command line
socketfile = '/tmp/mirrormanager_mirrorlist_server.sock'
cachefile = '/tmp/mirrorlist_cache.pkl'
internet2_netblocks_file = '/tmp/mirrormanager_i2_netblocks.txt'
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
country_continent_redirect_cache = {}

# our own private copy of country_continents to be edited
country_continents = GeoIP.country_continents

disabled_repositories = {}
host_bandwidth_cache = {}
host_country_cache = {}
file_details_cache = {}
hcurl_cache = {}

class OrderedNetblocks(list):
    def __contains__(self, item):
        if self.__len__() == 0:
            return False
        index = bisect.bisect(self, item)
        if index == 0:
            return False
        if item in self.__getitem__(index-1):
            return True
        return False

class OrderedIP(IP):
    """Override comparison function so that a list of our objects is in ascending order
    based on their starting IP, without regard to netblock size."""
    def __cmp__(self, other):
        if self.ip < other.ip:
            return -1
        elif self.ip > other.ip:
            return 1
        else:
            return 0


internet2_netblocks = OrderedNetblocks([])

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


##### Metalink Support #####
def metalink_failuredoc(directory, file):
    doc = ''
    doc += '<HTML>\n'
    doc += '<HEAD><TITLE>%s not found</TITLE></HEAD>\n'
    doc += '<BODY>%s/%s not found or has no metalink</BODY>' % (directory, file)
    doc += '</HTML>\n'
    return doc

def metalink(directory, file, hosts_and_urls):
    preference = 100
    # fixme pubdate format changed in later metalink specs/drafts.
    pubdate = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S %z")
    try:
        fdc = file_details_cache[directory]
        detailslist = fdc[file]
    except KeyError:
        return ('errordoc', 404, metalink_failuredoc(directory, file))

    def indent(n):
        return ' ' * n * 2

    doc = ''
    doc += '<?xml version="1.0" encoding="utf-8"?>\n'
    doc += '<metalink version="3.0" xmlns="http://www.metalinker.org/" type="dynamic" generator="mirrormanager" pubdate="%s" xmlns:mm0="http://fedorahosted.org/mirrormanager">\n' % pubdate
    doc += indent(1) + '<files>\n'
    doc += indent(2) + '<file name="%s/%s">\n' % (directory, file)
    y = detailslist[0]

    def details(y, indentlevel=2):
        doc = ''
        if y['timestamp'] is not None:
            doc += indent(indentlevel+1) + '<mm0:timestamp>%s</mm0:timestamp>\n' % y['timestamp']
        if y['size'] is not None:
            doc += indent(indentlevel+1) + '<size>%s</size>\n' % y['size']
        doc += indent(indentlevel+1) + '<verification>\n'
        if y['md5'] is not None:
            doc += indent(indentlevel+2) + '<hash type="md5">%s</hash>\n' % y['md5']
        if y['sha1'] is not None:
            doc += indent(indentlevel+2) + '<hash type="sha1">%s</hash>\n' % y['sha1']
        doc += indent(indentlevel+1) + '</verification>\n'
        return doc

    doc += details(y, 2)
    # there can be multiple files 
    if len(detailslist) > 1:
        doc += indent(3) + '<mm0:alternates>\n'
        for y in detailslist[1:]:
            doc += details(y,3)
        doc += indent(3) + '</mm0:alternates>\n'

    doc += indent(3) + '<resources maxconnections="1">\n'
    for (hostid, hcurls) in hosts_and_urls:
        for url in hcurls:
            protocol = url.split(':')[0]
            # fixme location is defined slightly different in the spec
            # investigate and fix accordingly
            doc += indent(4) + '<url protocol="%s" location="%s" preference="%s">' % (protocol, host_country_cache[hostid].upper(), preference)
            doc += url
            doc += '</url>\n'
        preference = max(preference-1, 1)
    doc += indent(3) + '</resources>\n'
    doc += indent(2) + '</file>\n'
    doc += indent(1) + '</files>\n'
    doc += '</metalink>\n'
    return ('metalink', 200, doc)

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

def trim_by_client_country(s, clientCountry):
    if clientCountry is None:
        return s
    r = s.copy()
    for hostid in s:
        if hostid in host_country_allowed_cache and \
               clientCountry not in host_country_allowed_cache[hostid]:
            r.remove(hostid)
    return r

def shuffle(s):
    l = []
    for hostid in s:
        item = (host_bandwidth_cache[hostid], hostid)
        l.append(item)
    newlist = weighted_shuffle(l)
    results = []
    for (bandwidth, hostid) in newlist:
        results.append(hostid)
    return results

def append_filename_to_results(file, hosts_and_urls):
    if file is None:
        return hosts_and_urls
    results = {}
    for hostid in host_and_urls.keys():
        
        hcurl = hcurl + '/%s' % (file)
        newresults.append((hostid, hcurl))
    return newresults

continents = {}

def handle_country_continent_redirect():
    global country_continents
    country_continents = GeoIP.country_continents
    for country, continent in country_continent_redirect_cache.iteritems():
        country_continents[country] = continent

def setup_continents():
    global continents
    continents = {}
    handle_country_continent_redirect()
    for c in country_continents.keys():
        continent = country_continents[c]
        if continent not in continents:
            continents[continent] = [c]
        else:
            continents[continent].append(c)
    
def do_global(kwargs, cache, clientCountry, header):
    c = trim_by_client_country(cache['global'], clientCountry)
    header += 'country = global '
    return (header, c)

def do_countrylist(kwargs, cache, clientCountry, requested_countries, header):

    def collapse(d):
        """ collapses a dict {key:set(hostids)} into a set of hostids """
        s = set()
        for country, hostids in d.iteritems():
            for hostid in hostids:
                s.add(hostid)
        return s

    country_cache = {}
    for c in requested_countries:
        if c in cache['byCountry']:
            country_cache[c] = cache['byCountry'][c]
            header += 'country = %s ' % c
    s = collapse(country_cache)
    s = trim_by_client_country(s, clientCountry)
    return (header, s)

def get_same_continent_countries(clientCountry, requested_countries):
    result = []
    for r in requested_countries:
        if r is not None:
            requestedCountries = [c.upper() for c in continents[country_continents[r]] \
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
    hostresults = set()
    client_ip = kwargs['client_ip']    
    if not kwargs.has_key('netblock') or kwargs['netblock'] == "1":
        hosts = client_netblocks(client_ip)
        if len(hosts) > 0:
            for hostid in hosts:
                hostresults.add(hostid)
                header += 'Using preferred netblock '
    return (header, hostresults)

def do_internet2(kwargs, cache, clientCountry, header):
    hostresults = set()
    client_ip = kwargs['client_ip']
    if OrderedIP(client_ip) in internet2_netblocks:
        header += 'Using Internet2 '
        if clientCountry is not None and clientCountry in cache['byCountryInternet2']:
            hostresults = cache['byCountryInternet2'][clientCountry]
            hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)

                
def do_geoip(kwargs, cache, clientCountry, header):
    hostresults = set()
    if clientCountry is not None and clientCountry in cache['byCountry']:
        hostresults = cache['byCountry'][clientCountry]
        header += 'country = %s ' % clientCountry
        hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)

def add_host_to_cache(cache, hostid, hcurl):
    if hostid not in cache:
        cache[hostid] = [hcurl]
    else:
        cache[hostid].append(hcurl)
    return cache

def append_path(hosts, cache, file):
    """ given a list of hosts, return a list of objects:
    [(hostid, [hcurls]), ... ]
    in the same order, appending file if it's not None"""
    subpath = None
    results = []
    if 'subpath' in cache:
        subpath = cache['subpath']
    for hostid in hosts:
        hcurls = []
        for hcurl_id in cache['byHostId'][hostid]:
            s = hcurl_cache[hcurl_id]
            if subpath is not None:
                s += "/" + subpath
            if file is not None:
                s += "/" + file
            hcurls.append(s)
        results.append((hostid, hcurls))
    return results

def trim_to_preferred_protocols(hosts_and_urls):
    """ remove all but http and ftp URLs,
    and if both http and ftp are offered,
    leave only http. Return [(hostid, url), ...] """
    results = []
    try_protocols = ('https', 'http', 'ftp')
    for (hostid, hcurls) in hosts_and_urls:
        protocols = {}
        url = None
        for hcurl in hcurls:
            for p in try_protocols:
                if hcurl.startswith(p+':'):
                    protocols[p] = hcurl
                    
        for p in try_protocols:
            if p in protocols:
                url = protocols[p]
                break
 
        if url is not None:
            results.append((hostid, url))
    return results


def do_mirrorlist(kwargs):
    if not (kwargs.has_key('repo') and kwargs.has_key('arch')) and not kwargs.has_key('path'):
        return dict(resulttype='mirrorlist', returncode=200, results=[], message='# either path=, or repo= and arch= must be specified')

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
                return dict(resulttype='mirrorlist', returncode=200, results=[], message=header + 'error: invalid path')
        dir = '/'.join(sdir)
    else:
        if u'source' in kwargs['repo']:
            kwargs['arch'] = u'source'
        repo = repo_redirect.get(kwargs['repo'], kwargs['repo'])
        arch = kwargs['arch']
        header = "# repo = %s arch = %s " % (repo, arch)

        if repo in disabled_repositories:
            return dict(resulttype='mirrorlist', returncode=200, results=[], message=header + 'repo disabled')
        try:
            dir = repo_arch_to_directoryname[(repo, arch)]
            if 'metalink' in kwargs and kwargs['metalink']:
                dir += '/repodata'
                file = 'repomd.xml'
            cache = mirrorlist_cache[dir]
        except KeyError:
            return dict(resulttype='mirrorlist', returncode=200, results=[], message=header + 'error: invalid repo or arch')


    ordered_mirrorlist = cache.get('ordered_mirrorlist', default_ordered_mirrorlist)
    done = 0
    netblock_results = set()
    internet2_results = set()
    country_results = set()
    geoip_results = set()
    continent_results = set()
    global_results = set()

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
    
    if not done:
        header, internet2_results = do_internet2(kwargs, cache, clientCountry, header)
        if len(internet2_results) + len(netblock_results) >= 3:
            if not ordered_mirrorlist:
                done = 1

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
            done = 1

    if not done:
        header, global_results = do_global(kwargs, cache, clientCountry, header)

    def _random_shuffle(s):
        l = list(s)
        random.shuffle(l)
        return l
    
    netblock_hosts    = _random_shuffle(netblock_results)
    internet2_hosts   = _random_shuffle(internet2_results)
    country_hosts     = shuffle(country_results)
    geoip_hosts       = shuffle(geoip_results)
    continent_hosts   = shuffle(continent_results)
    global_hosts      = shuffle(global_results)

    allhosts = uniqueify(netblock_hosts + internet2_hosts + country_hosts + geoip_hosts + continent_hosts + global_hosts)
    hosts_and_urls = append_path(allhosts, cache, file)

    if 'metalink' in kwargs and kwargs['metalink']:
        (resulttype, returncode, results)=metalink(dir, file, hosts_and_urls)
        d = dict(message=None, resulttype=resulttype, returncode=returncode, results=results)
        return d

    else:
        host_url_list = trim_to_preferred_protocols(hosts_and_urls)
        d = dict(message=header, resulttype='mirrorlist', returncode=200, results=host_url_list)
        return d


def setup_internet2_netblocks():
    i2_netblocks = OrderedNetblocks([])
    n = []
    if internet2_netblocks_file is not None:
        try:
            f = open(internet2_netblocks_file, 'r')
            for l in f.readlines():
                s = l.split()
                start, mask = s[0].split('/')
                n.append((int(mask), start))
            f.close()
        except:
            pass
        # This ensures we fill in the biggest netblocks first, and don't include
        # smaller netblocks that are fully contained in an existing netblock.
        n.sort()
        for l in n:
            ip = OrderedIP("%s/%s" % (l[1], l[0]))
            if ip not in i2_netblocks:
                bisect.insort(i2_netblocks, ip)
    global internet2_netblocks
    internet2_netblocks = i2_netblocks

def read_caches():
    global mirrorlist_cache
    global host_netblock_cache
    global host_country_allowed_cache
    global repo_arch_to_directoryname
    global repo_redirect
    global country_continent_redirect_cache
    global disabled_repositories
    global host_bandwidth_cache
    global host_country_cache
    global file_details_cache
    global hcurl_cache

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
    if 'repo_redirect_cache' in data:
        repo_redirect = data['repo_redirect_cache']
    if 'country_continent_redirect_cache' in data:
        country_continent_redirect_cache = data['country_continent_redirect_cache']
    if 'disabled_repositories' in data:
        disabled_repositories = data['disabled_repositories']
    if 'host_bandwidth_cache' in data:
        host_bandwidth_cache = data['host_bandwidth_cache']
    if 'host_country_cache' in data:
        host_country_cache = data['host_country_cache']
    if 'file_details_cache' in data:
        file_details_cache = data['file_details_cache']
    if 'hcurl_cache' in data:
        hcurl_cache = data['hcurl_cache']

    del data
    setup_continents()
    setup_internet2_netblocks()

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
            r = do_mirrorlist(d)
            message = r['message']
            results = r['results']
            returncode = r['returncode']
            resulttype = r['resulttype']
        except:
            message='# Server Error'
            results = []
            resulttype = 'mirrorlist'
            returncode = 500
        del d
        del p

        try:
            p = pickle.dumps({'message':message, 'resulttype':resulttype, 'results':results, 'returncode':returncode})
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

def parse_args():
    global cachefile
    global socketfile
    global internet2_netblocks_file
    opts, args = getopt.getopt(sys.argv[1:], "c:i:s:", ["cache", "internet2_netblocks", "socket"])
    for option, argument in opts:
        if option in ("-c", "--cache"):
            cachefile = argument
        if option in ("-i", "--internet2_netblocks"):
            internet2_netblocks_file = argument
        if option in ("-s", "--socket"):
            socketfile = argument

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
