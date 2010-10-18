#!/usr/bin/python
#
# Copyright (c) 2007,2008,2009 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

from SocketServer import StreamRequestHandler, ForkingMixIn, UnixStreamServer, BaseServer
import cPickle as pickle
import os, sys, signal, random, socket, getopt
from string import zfill, atoi
import datetime
import time
import radix

from IPy import IP
import GeoIP
from weighted_shuffle import weighted_shuffle

# can be overridden on the command line
socketfile = '/var/run/mirrormanager/mirrorlist_server.sock'
cachefile = '/var/lib/mirrormanager/mirrorlist_cache.pkl'
internet2_netblocks_file = '/var/lib/mirrormanager/i2_netblocks.txt'
global_netblocks_file = '/var/lib/mirrormanager/global_netblocks.txt'
logfile = None
debug = False
# at a point in time when we're no longer serving content for versions
# that don't use yum prioritymethod=fallback
# (e.g. after Fedora 7 is past end-of-life)
# then we can set this value to True
# this only affects results requested using path=...
# for dirs which aren't repositories (such as iso/)
# because we don't know the Version associated with that dir here.
default_ordered_mirrorlist = False

gipv4 = None
gipv6 = None

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
asn_host_cache = {}
internet2_tree = radix.Radix()
global_tree = radix.Radix()
location_cache = {}

def lookup_ip_asn(tree, ip):
    """ @t is a radix tree
        @ip is an IPy.IP object which may be contained in an entry in l
        """
    node = tree.search_best(str(ip))
    if node is None:
        return None
    return node.data['asn']


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

def metalink_header():
    # fixme add alternate format pubdate when specified
    pubdate = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    doc = ''
    doc += '<?xml version="1.0" encoding="utf-8"?>\n'
    doc += '<metalink version="3.0" xmlns="http://www.metalinker.org/"'
    doc += ' type="dynamic"'
    doc += ' pubdate="%s"' % pubdate
    doc += ' generator="mirrormanager"'
    doc += ' xmlns:mm0="http://fedorahosted.org/mirrormanager"'
    doc += '>\n'
    return doc

def metalink_failuredoc(message=None):
    doc = metalink_header()
    if message is not None:
        doc += '<!--\n'
        doc += message + '\n'
        doc += '-->\n'
    doc += '</metalink>\n'
    return doc

def metalink_file_not_found(directory, file):
    message = '%s/%s not found or has no metalink' % (directory, file)
    return metalink_failuredoc(message)

def metalink(cache, directory, file, hosts_and_urls):
    preference = 100
    try:
        fdc = file_details_cache[directory]
        detailslist = fdc[file]
    except KeyError:
        return ('metalink', 404, metalink_file_not_found(directory, file))

    def indent(n):
        return ' ' * n * 2

    doc = metalink_header()
    doc += indent(1) + '<files>\n'
    doc += indent(2) + '<file name="%s">\n' % (file)
    y = detailslist[0]

    def details(y, indentlevel=2):
        doc = ''
        if y['timestamp'] is not None:
            doc += indent(indentlevel+1) + '<mm0:timestamp>%s</mm0:timestamp>\n' % y['timestamp']
        if y['size'] is not None:
            doc += indent(indentlevel+1) + '<size>%s</size>\n' % y['size']
        doc += indent(indentlevel+1) + '<verification>\n'
        hashes = ('md5', 'sha1', 'sha256', 'sha512')
        for h in hashes:
            if y[h] is not None:
                doc += indent(indentlevel+2) + '<hash type="%s">%s</hash>\n' % (h, y[h])
        doc += indent(indentlevel+1) + '</verification>\n'
        return doc

    doc += details(y, 2)
    # there can be multiple files 
    if len(detailslist) > 1:
        doc += indent(3) + '<mm0:alternates>\n'
        for y in detailslist[1:]:
            doc += indent(4) + '<mm0:alternate>\n'
            doc += details(y,5)
            doc += indent(4) + '</mm0:alternate>\n'
        doc += indent(3) + '</mm0:alternates>\n'

    doc += indent(3) + '<resources maxconnections="1">\n'
    for (hostid, hcurls) in hosts_and_urls:
        private = ''
        if hostid not in cache['global']:
            private = 'mm0:private="True"'
        for url in hcurls:
            protocol = url.split(':')[0]
            # FIXME January 2010
            # adding protocol= here is not part of the Metalink 3.0 spec,
            # but MirrorManager 1.2.6 used it accidentally, as did yum 3.2.20-3 as released
            # in Fedora 8, 9, and 10.  After those three are EOL (~January 2010), the
            # extra protocol= can be removed.
            doc += indent(4) + '<url protocol="%s" type="%s" location="%s" preference="%s" %s>' % (protocol, protocol, host_country_cache[hostid].upper(), preference, private)
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
        if r in country_continents:
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
        for hostid in hosts:
            if hostid in cache['byHostId']:
                hostresults.add(hostid)
                header += 'Using preferred netblock '
    return (header, hostresults)

def do_internet2(kwargs, cache, clientCountry, header):
    hostresults = set()
    client_ip = kwargs['client_ip']
    if client_ip == 'unknown':
        return (header, hostresults)
    try:
        ip = IP(client_ip)
    except:
        return (header, hostresults)
    asn = lookup_ip_asn(internet2_tree, ip)
    if asn is not None:
        header += 'Using Internet2 '
        if clientCountry is not None and clientCountry in cache['byCountryInternet2']:
            hostresults = cache['byCountryInternet2'][clientCountry]
            hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)

def do_asn(kwargs, cache, header):
    hostresults = set()
    client_ip = kwargs['client_ip']
    if client_ip == 'unknown':
        return (header, hostresults)
    try:
        ip = IP(client_ip)
    except:
        return (header, hostresults)
    asn = lookup_ip_asn(global_tree, ip)
    if asn is not None and asn in asn_host_cache:
        for hostid in asn_host_cache[asn]:
            if hostid in cache['byHostId']:
                hostresults.add(hostid)
                header += 'Using ASN %s ' % asn
    return (header, hostresults)
                
def do_geoip(kwargs, cache, clientCountry, header):
    hostresults = set()
    if clientCountry is not None and clientCountry in cache['byCountry']:
        hostresults = cache['byCountry'][clientCountry]
        header += 'country = %s ' % clientCountry
        hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)

def do_location(kwargs, header):
    hostresults = set()
    if 'location' in kwargs and kwargs['location'] in location_cache:
        hostresults = set(location_cache[kwargs['location']])
        header += "Using location %s " % kwargs['location']
    return (header, hostresults)

def add_host_to_cache(cache, hostid, hcurl):
    if hostid not in cache:
        cache[hostid] = [hcurl]
    else:
        cache[hostid].append(hcurl)
    return cache

def append_path(hosts, cache, file, pathIsDirectory=False):
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
            if file is None and pathIsDirectory:
                s += "/"
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
    global debug
    global logfile

    def return_error(kwargs, message='', returncode=200):
        d = dict(returncode=returncode, message=message, resulttype='mirrorlist', results=[])
        if 'metalink' in kwargs and kwargs['metalink']:
            d['resulttype'] = 'metalink'
            d['results'] = metalink_failuredoc(message)
        return d

    if not (kwargs.has_key('repo') and kwargs.has_key('arch')) and not kwargs.has_key('path'):
        return return_error(kwargs, message='# either path=, or repo= and arch= must be specified')

    file = None
    cache = None
    pathIsDirectory = False
    if kwargs.has_key('path'):
        path = kwargs['path'].strip('/')

	# Strip duplicate "//" from the path
        path = path.replace('//', '/')

        header = "# path = %s " % (path)

        sdir = path.split('/')
        try:
            # path was to a directory
            cache = mirrorlist_cache['/'.join(sdir)]
            pathIsDirectory=True
        except KeyError:
            # path was to a file, try its directory
            file = sdir[-1]
            sdir = sdir[:-1]
            try:
                cache = mirrorlist_cache['/'.join(sdir)]
            except KeyError:
                return return_error(kwargs, message=header + 'error: invalid path')
        dir = '/'.join(sdir)
    else:
        if u'source' in kwargs['repo']:
            kwargs['arch'] = u'source'
        repo = repo_redirect.get(kwargs['repo'], kwargs['repo'])
        arch = kwargs['arch']
        header = "# repo = %s arch = %s " % (repo, arch)

        if repo in disabled_repositories:
            return return_error(kwargs, message=header + 'repo disabled')
        try:
            dir = repo_arch_to_directoryname[(repo, arch)]
            if 'metalink' in kwargs and kwargs['metalink']:
                dir += '/repodata'
                file = 'repomd.xml'
            else:
                pathIsDirectory=True
            cache = mirrorlist_cache[dir]
        except KeyError:
            repos = repo_arch_to_directoryname.keys()
            repos.sort()
            repo_information = header + "error: invalid repo or arch\n"
            repo_information += "# following repositories are available:\n"
            for i in repos:
                if i[0] is not None and i[1] is not None:
                    repo_information += "# repo=%s, arch=%s\n" % i
            return return_error(kwargs, message=repo_information)


    ordered_mirrorlist = cache.get('ordered_mirrorlist', default_ordered_mirrorlist)
    done = 0
    location_results = set()
    netblock_results = set()
    asn_results = set()
    internet2_results = set()
    country_results = set()
    geoip_results = set()
    continent_results = set()
    global_results = set()

    header, location_results = do_location(kwargs, header)

    requested_countries = []
    if kwargs.has_key('country'):
        requested_countries = uniqueify([c.upper() for c in kwargs['country'].split(',') ])

    # if they specify a country, don't use netblocks or ASN
    if not 'country' in kwargs:
        header, netblock_results = do_netblocks(kwargs, cache, header)
        if len(netblock_results) > 0:
            if not ordered_mirrorlist:
                done=1

        if not done:
            header, asn_results = do_asn(kwargs, cache, header)
            if len(asn_results) + len(netblock_results) >= 3:
                if not ordered_mirrorlist:
                    done = 1

    client_ip = kwargs['client_ip']
    clientCountry = None
    # attempt IPv6, then IPv6 6to4 as IPv4, then Teredo, then IPv4
    try:
        ip = IP(client_ip)
        if ip.version() == 6:
            if gipv6 is not None:
                clientCountry = gipv6.country_code_by_addr_v6(ip.strNormal())
            if clientCountry is None:
                # Try the IPv6-to-IPv4 translation schemes
                for scheme in (convert_6to4_v4, convert_teredo_v4):
                    result = scheme(ip)
                    if result is not None:
                        ip = result
                        break
        if ip.version() == 4 and gipv4 is not None:
            clientCountry = gipv4.country_code_by_addr(ip.strNormal())
    except:
        pass

    if clientCountry is None:
        print_client_country = "N/A"
    else:
        print_client_country = clientCountry

    if debug:
        if kwargs.has_key('repo') and kwargs.has_key('arch'):
            print ("IP: " + client_ip +
                   "; DATE: " + time.strftime("%Y-%m-%d") +
                   "; COUNTRY: " + print_client_country + 
                   "; REPO: " + kwargs['repo'] + 
                   "; ARCH: " + kwargs['arch'])

    if logfile is not None:
        if kwargs.has_key('repo') and kwargs.has_key('arch'):
            logfile.write("IP: " + client_ip +
                          "; DATE: " + time.strftime("%Y-%m-%d") +
                          "; COUNTRY: " + print_client_country +
                          "; REPO: " + kwargs['repo'] +
                          "; ARCH: " + kwargs['arch'] + "\n")
            logfile.flush()

    if not done:
        header, internet2_results = do_internet2(kwargs, cache, clientCountry, header)
        if len(internet2_results) + len(netblock_results) + len(asn_results) >= 3:
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

    def _ordered_netblocks(s):
        def ipy_len(ip):
            return ip.len()
        v4_netblocks = []
        v6_netblocks = []
        for n in s:
            if n.version() == 4:
                v4_netblocks.append(n)
            elif n.version() == 6:
                v6_netblocks.append(n)
        # mix up the order, as sort will preserve same-key ordering
        random.shuffle(v4_netblocks)
        v4_netblocks.sort(key=ipy_len)
        random.shuffle(v6_netblocks)
        v6_netblocks.sort(key=ipy_len)
        return v6_netblocks + v4_netblocks
    
    location_hosts    = _random_shuffle(location_results)
    netblock_hosts    = _ordered_netblocks(netblock_results)
    asn_hosts         = _random_shuffle(asn_results)
    internet2_hosts   = _random_shuffle(internet2_results)
    country_hosts     = shuffle(country_results)
    geoip_hosts       = shuffle(geoip_results)
    continent_hosts   = shuffle(continent_results)
    global_hosts      = shuffle(global_results)

    allhosts = uniqueify(location_hosts + netblock_hosts + asn_hosts + internet2_hosts + country_hosts + geoip_hosts + continent_hosts + global_hosts)
    hosts_and_urls = append_path(allhosts, cache, file, pathIsDirectory=pathIsDirectory)

    if 'metalink' in kwargs and kwargs['metalink']:
        (resulttype, returncode, results)=metalink(cache, dir, file, hosts_and_urls)
        d = dict(message=None, resulttype=resulttype, returncode=returncode, results=results)
        return d

    else:
        host_url_list = trim_to_preferred_protocols(hosts_and_urls)
        d = dict(message=header, resulttype='mirrorlist', returncode=200, results=host_url_list)
        return d


def setup_netblocks(netblocks_file):

    tree = radix.Radix()
    if netblocks_file is not None:
        try:
            f = open(netblocks_file, 'r')
        except:
            return tree
        for l in f:
            try:
                s = l.split()
                start, mask = s[0].split('/')
                mask = int(mask)
                if mask == 0: continue
                asn = int(s[1])
                node = tree.add(s[0])
                node.data['asn'] = asn
            except:
                pass
        f.close()

    return tree

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
    global asn_host_cache
    global location_cache

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
    if 'asn_host_cache' in data:
        asn_host_cache = data['asn_host_cache']
    if 'location_cache' in data:
        location_cache = data['location_cache']

    del data
    setup_continents()
    global internet2_tree
    global global_tree

    del internet2_tree
    del global_tree

    internet2_tree = setup_netblocks(internet2_netblocks_file)
    global_tree    = setup_netblocks(global_netblocks_file)

def errordoc(metalink, message):
    if metalink:
        doc = metalink_failuredoc(message)
    else:
        doc = message
    return doc

class MirrorlistHandler(StreamRequestHandler):
    def handle(self):
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
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
            try:
                r = do_mirrorlist(d)
            except:
                raise
            message = r['message']
            results = r['results']
            resulttype = r['resulttype']
            returncode = r['returncode']
        except:
            message=u'# Bad Request'
            returncode = 400
            results = []
            resulttype = 'mirrorlist'
            if d['metalink']:
                resulttype = 'metalink'
                results = errordoc(d['metalink'], message)
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
    global logfile
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    if signum == signal.SIGHUP:
        if debug:
            print "Got SIGHUP; reloading data"
        open_geoip_databases()
        read_caches()
        if logfile is not None:
            name = logfile.name
            logfile.close()
            logfile = open(name, 'a')
    signal.signal(signal.SIGHUP, sighup_handler)

class ForkingUnixStreamServer(ForkingMixIn, UnixStreamServer):
    request_queue_size = 300
    def finish_request(self, request, client_address):
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        BaseServer.finish_request(self, request, client_address)

def parse_args():
    global cachefile
    global socketfile
    global internet2_netblocks_file
    global global_netblocks_file
    global debug
    global logfile
    opts, args = getopt.getopt(sys.argv[1:], "c:i:g:s:dl:",
                               ["cache", "internet2_netblocks", "global_netblocks", "socket", "debug", "log="])
    for option, argument in opts:
        if option in ("-c", "--cache"):
            cachefile = argument
        if option in ("-i", "--internet2_netblocks"):
            internet2_netblocks_file = argument
        if option in ("-g", "--global_netblocks"):
            global_netblocks_file = argument
        if option in ("-s", "--socket"):
            socketfile = argument
        if option in ("-l", "--log"):
            try:
                logfile = open(argument, 'a')
            except:
                logfile = None
        if option in ("-d", "--debug"):
            debug = True
            print "debug output enabled"

def open_geoip_databases():
    global gipv4
    global gipv6
    try:
        gipv4 = GeoIP.open("/usr/share/GeoIP/GeoIP.dat", GeoIP.GEOIP_STANDARD)
    except:
        gipv4=None
    try:
        gipv6 = GeoIP.open("/usr/share/GeoIP/GeoIPv6.dat", GeoIP.GEOIP_STANDARD)
    except:
        gipv6=None

def convert_6to4_v4(ip):
    all_6to4 = IP('2002::/16')
    if ip.version() != 6 or ip not in all_6to4:
        return None
    parts=ip.strNormal().split(':')

    ab = int(parts[1],16)
    a = (ab >> 8) & 0xFF
    b = ab & 0xFF
    cd = int(parts[2],16)
    c = (cd >> 8) & 0xFF
    d = cd & 0xFF

    v4addr = '%d.%d.%d.%d' % (a,b,c,d)
    return IP(v4addr)

def convert_teredo_v4(ip):
    teredo_std = IP('2001::/32')
    teredo_xp  = IP('3FFE:831F::/32')
    if ip.version() != 6 or (ip not in teredo_std and ip not in teredo_xp):
        return None
    parts=ip.strNormal().split(':')

    ab = int(parts[6],16)
    a = ((ab >> 8) & 0xFF) ^ 0xFF
    b = (ab & 0xFF) ^ 0xFF
    cd = int(parts[7],16)
    c = ((cd >> 8) & 0xFF) ^ 0xFF
    d = (cd & 0xFF) ^ 0xFF

    v4addr = '%d.%d.%d.%d' % (a,b,c,d)
    return IP(v4addr)

def main():
    global logfile
    parse_args()
    oldumask = os.umask(0)
    try:
        os.unlink(socketfile)
    except:
        pass

    open_geoip_databases()
    read_caches()
    signal.signal(signal.SIGHUP, sighup_handler)
    ss = ForkingUnixStreamServer(socketfile, MirrorlistHandler)
    ss.serve_forever()

    try:
        os.unlink(socketfile)
    except:
        pass

    if logfile is not None:
        try:
            logfile.close()
        except:
            pass

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(-1)
