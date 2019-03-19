#!/usr/bin/env python
#
# Copyright (c) 2007-2013 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

# standard library modules in alphabetical order
from collections import defaultdict
import csv
import datetime
import getopt
import logging
import logging.handlers
import os
import random
try:
    import cPickle as pickle
except ImportError:
    import pickle
import select
import signal
import socket
try:
    from socketserver import (StreamRequestHandler, ThreadingMixIn,
                              UnixStreamServer, BaseServer)
except ImportError:
    from SocketServer import (StreamRequestHandler, ThreadingMixIn,
                              UnixStreamServer, BaseServer)
import sys
import time
import traceback

try:
    import threading
except ImportError:
    import dummy_threading as threading

# not-so-standard library modules that this program needs
from IPy import IP
import geoip2.database
import radix
from weighted_shuffle import weighted_shuffle
import mirrormanager_pb2

# can be overridden on the command line
pidfile = '/var/run/mirrormanager/mirrorlist_server.pid'
socketfile = '/var/run/mirrormanager/mirrorlist_server.sock'
cachefile = '/var/lib/mirrormanager/mirrorlist_cache.pkl'
internet2_netblocks_file = '/var/lib/mirrormanager/i2_netblocks.txt'
global_netblocks_file = '/var/lib/mirrormanager/global_netblocks.txt'
country_continent_csv = '/usr/share/mirrormanager2/country_continent.csv'
logfile = None
# If not at least 'minimum' mirrors are found for a country/continent,
# mirrors from the global list are appended to the country/continent list
minimum = int(5)
must_die = False
# at a point in time when we're no longer serving content for versions
# that don't use yum prioritymethod=fallback
# (e.g. after Fedora 7 is past end-of-life)
# then we can set this value to True
# this only affects results requested using path=...
# for dirs which aren't repositories (such as iso/)
# because we don't know the Version associated with that dir here.
default_ordered_mirrorlist = False

# our own private copy of country_continents to be edited
country_continents = {}

## Set up our syslog data.
syslogger = logging.getLogger('mirrormanager')
syslogger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(
    address='/dev/log',
    facility=logging.handlers.SysLogHandler.LOG_LOCAL4)
syslogger.addHandler(handler)

# The entire in-memory structure
database = {}


def read_country_continents():
    local_country_continents = {}
    with open(country_continent_csv, mode='r') as infile:
        reader = csv.reader(infile)
        local_country_continents = {rows[0]: rows[1] for rows in reader}
    return local_country_continents


def lookup_ip_asn(tree, ip):
    """ @t is a radix tree
        @ip is an IPy.IP object which may be contained in an entry in l
        """
    node = tree.search_best(ip.strNormal())
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
        if marker in seen:
            continue
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
        fdc = database['file_details_cache'][directory]
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
            doc += indent(indentlevel+1) \
                + '<mm0:timestamp>%s</mm0:timestamp>\n' % y['timestamp']
        if y['size'] is not None:
            doc += indent(indentlevel+1) + '<size>%s</size>\n' % y['size']
        doc += indent(indentlevel+1) + '<verification>\n'
        hashes = ('md5', 'sha1', 'sha256', 'sha512')
        for h in hashes:
            if y[h] is not None:
                doc += indent(indentlevel+2) \
                    + '<hash type="%s">%s</hash>\n' % (h, y[h])
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
            # but MirrorManager 1.2.6 used it accidentally, as did
            # yum 3.2.20-3 as released in Fedora 8, 9, and 10.  After those
            # three are EOL (~January 2010), the extra protocol= can be
            # removed.
            doc += indent(4) + \
                '<url protocol="%s" type="%s" location="%s" '\
                'preference="%s" %s>' % (
                    protocol, protocol, database['host_country_cache'][hostid].upper(),
                    preference, private)
            doc += url
            doc += '</url>\n'
        preference = max(preference-1, 1)
    doc += indent(3) + '</resources>\n'
    doc += indent(2) + '</file>\n'
    doc += indent(1) + '</files>\n'
    doc += '</metalink>\n'
    return ('metalink', 200, doc)


def tree_lookup(tree, ip, field, maxResults=None):
    # Lookup up to maxResults matching prefixes from the tree
    # returns a list of tuples (prefix, data)
    result = []
    len_data = 0
    if ip is None:
        return result
    for node in tree.search_covering(ip.strNormal()):
        prefix = node.prefix
        if type(node.data[field]) == list:
            len_data += len(node.data[field])
        else:
            len_data += 1
        t = (prefix, node.data[field],)
        result.append(t)
        if maxResults is not None and len_data >= maxResults:
            break
    return result


def trim_by_client_country(s, clientCountry):
    if clientCountry is None:
        return s
    r = s.copy()
    for hostid in s:
        if hostid in database['host_country_allowed_cache'] and \
               clientCountry not in database['host_country_allowed_cache'][hostid]:
            r.remove(hostid)
    return r


def shuffle(s):
    l = []
    for hostid in s:
        item = (database['host_bandwidth_cache'][hostid], hostid)
        l.append(item)
    newlist = weighted_shuffle(l)
    results = []
    for (bandwidth, hostid) in newlist:
        results.append(hostid)
    return results


continents = {}

def handle_country_continent_redirect(new_db):
    new_country_continents = read_country_continents()
    for country, continent in new_db['country_continent_redirect_cache'].items():
        new_country_continents[country] = continent
    global country_continents
    country_continents = new_country_continents


def setup_continents(new_db):
    new_continents = defaultdict(list)
    handle_country_continent_redirect(new_db)
    for c, continent in country_continents.items():
        new_continents[continent].append(c)
    global continents
    continents = new_continents


def do_global(kwargs, cache, clientCountry, header):
    c = trim_by_client_country(cache['global'], clientCountry)
    header += 'country = global '
    return (header, c)


def do_countrylist(kwargs, cache, clientCountry, requested_countries, header):

    def collapse(d):
        """ collapses a dict {key:set(hostids)} into a set of hostids """
        s = set()
        for country, hostids in d.items():
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
            requestedCountries = [
                c.upper() for c in continents[country_continents[r]]
                if c != clientCountry]
            result.extend(requestedCountries)
    result = uniqueify(result)
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
    return do_countrylist(
        kwargs, cache, clientCountry, requested_countries, header)


def do_netblocks(kwargs, cache, header):
    hostresults = set()
    if 'netblock' not in kwargs or kwargs['netblock'] == "1":
        tree_results = tree_lookup(database['host_netblocks_tree'], kwargs['IP'], 'hosts')
        for (prefix, hostids) in tree_results:
            for hostid in hostids:
                if hostid in cache['byHostId']:
                    hostresults.add((prefix, hostid,))
                    header += 'Using preferred netblock '
    return (header, hostresults)


def do_internet2(kwargs, cache, clientCountry, header):
    hostresults = set()
    ip = kwargs['IP']
    if ip is None:
        return (header, hostresults)
    asn = lookup_ip_asn(database['internet2_tree'], ip)
    if asn is not None:
        header += 'Using Internet2 '
        if clientCountry is not None \
                and clientCountry in cache['byCountryInternet2']:
            hostresults = cache['byCountryInternet2'][clientCountry]
            hostresults = trim_by_client_country(hostresults, clientCountry)
    return (header, hostresults)


def do_asn(kwargs, cache, header):
    hostresults = set()
    ip = kwargs['IP']
    if ip is None:
        return (header, hostresults)
    asn = lookup_ip_asn(database['global_tree'], ip)
    if asn is not None and asn in database['asn_host_cache']:
        for hostid in database['asn_host_cache'][asn]:
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
    if 'location' in kwargs and kwargs['location'] in database['location_cache']:
        hostresults = set(database['location_cache'][kwargs['location']])
        header += "Using location %s " % kwargs['location']
    return (header, hostresults)


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
            s = database['hcurl_cache'][hcurl_id]
            if subpath is not None:
                s += "/" + subpath
            if file is None and pathIsDirectory:
                s += "/"
            if file is not None:
                if not s.endswith('/'):
                    s += "/"
                s += file
            hcurls.append(s)
        results.append((hostid, hcurls))
    return results


def trim_to_preferred_protocols(hosts_and_urls, try_protocols=None):
    """ Remove all protocols but https, http and ftp,
    and if both http and ftp are offered, leave only http.
    If try_protocols is not empty only the specified
    protocols will be used.
    Return [(hostid, url), ...] """
    results = []
    if not try_protocols:
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
                url = [protocols[p]]
                break

        if url is not None:
            results.append((hostid, url))
    return results


def client_ip_to_country(ip):
    clientCountry = None
    if ip is None:
        return None

    # lookup in the cache first
    tree_results = tree_lookup(
        database['netblock_country_tree'], ip, 'country', maxResults=1)
    if len(tree_results) > 0:
        (prefix, clientCountry) = tree_results[0]
        return clientCountry

    # attempt IPv6, then IPv6 6to4 as IPv4, then Teredo, then IPv4
    try:
        if ip.version() == 6:
            if database['geoip'] is not None:
                clientCountry = (database['geoip']
                                 .country(ip.strNormal())
                                 .country.iso_code)
            if clientCountry is None:
                # Try the IPv6-to-IPv4 translation schemes
                for scheme in (convert_6to4_v4, convert_teredo_v4):
                    result = scheme(ip)
                    if result is not None:
                        ip = result
                        break
        if ip.version() == 4 and database['geoip'] is not None:
            clientCountry = (database['geoip']
                             .country(ip.strNormal())
                             .country.iso_code)
    except:
        pass
    return clientCountry


def do_mirrorlist(kwargs):
    global logfile

    def return_error(kwargs, message='', returncode=200):
        d = dict(
            returncode=returncode,
            message=message,
            resulttype='mirrorlist',
            results=[])
        if 'metalink' in kwargs and kwargs['metalink']:
            d['resulttype'] = 'metalink'
            d['results'] = metalink_failuredoc(message)
        return d

    if not ('repo' in kwargs and 'arch' in kwargs
            or 'path' in kwargs):
        return return_error(
            kwargs,
            message='# either path=, or repo= and arch= must be specified')

    file = None
    cache = None
    pathIsDirectory = False
    if 'path' in kwargs:
        path = kwargs['path'].strip('/')

    # Strip duplicate "//" from the path
        path = path.replace('//', '/')

        header = "# path = %s " % (path)

        sdir = path.split('/')
        try:
            # path was to a directory
            cache = database['mirrorlist_cache']['/'.join(sdir)]
            pathIsDirectory=True
        except KeyError:
            # path was to a file, try its directory
            file = sdir[-1]
            sdir = sdir[:-1]
            try:
                cache = database['mirrorlist_cache']['/'.join(sdir)]
            except KeyError:
                return return_error(
                    kwargs, message=header + 'error: invalid path')
        dir = '/'.join(sdir)
    else:
        if u'source' in kwargs['repo']:
            kwargs['arch'] = u'source'
        repo = database['repo_redirect'].get(kwargs['repo'], kwargs['repo'])
        arch = kwargs['arch']
        header = "# repo = %s arch = %s " % (repo, arch)

        if repo in database['disabled_repositories']:
            return return_error(kwargs, message=header + 'repo disabled')
        try:
            dir = database['repo_arch_to_directoryname'][(repo, arch)]
            if 'metalink' in kwargs and kwargs['metalink']:
                dir += '/repodata'
                file = 'repomd.xml'
            else:
                pathIsDirectory=True
            cache = database['mirrorlist_cache'][dir]
        except KeyError:
            repos = database['repo_arch_to_directoryname'].keys()
            repos.sort()
            repo_information = header + "error: invalid repo or arch\n"
            repo_information += "# following repositories are available:\n"
            for i in repos:
                if i[0] is not None and i[1] is not None:
                    repo_information += "# repo=%s&arch=%s\n" % i
            return return_error(kwargs, message=repo_information)

    # set kwargs['IP'] exactly once
    try:
        kwargs['IP'] = IP(kwargs['client_ip'])
    except:
        kwargs['IP'] = None

    ordered_mirrorlist = cache.get(
        'ordered_mirrorlist', default_ordered_mirrorlist)
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
    if 'country' in kwargs:
        requested_countries = uniqueify(
            [c.upper() for c in kwargs['country'].split(',') ])

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

    clientCountry = client_ip_to_country(kwargs['IP'])

    if clientCountry is None:
        print_client_country = "N/A"
    else:
        print_client_country = clientCountry

    if logfile and 'repo' in kwargs and 'arch' in kwargs:
        msg = "IP: %s; DATE: %s; COUNTRY: %s; REPO: %s; ARCH: %s\n"  % (
            (kwargs['IP'] or 'None'), time.strftime("%Y-%m-%d"),
            print_client_country, kwargs['repo'], kwargs['arch'])

        logfile.write(msg)
        logfile.flush()

    if not done:
        header, internet2_results = do_internet2(
            kwargs, cache, clientCountry, header)
        if len(internet2_results) + len(netblock_results) + len(asn_results) >= 3:
            if not ordered_mirrorlist:
                done = 1

    if not done and 'country' in kwargs:
        header, country_results  = do_country(
            kwargs, cache, clientCountry, requested_countries, header)
        if len(country_results) == 0:
            header, continent_results = do_continent(
                kwargs, cache, clientCountry, requested_countries, header)
        done = 1

    if not done:
        header, geoip_results = do_geoip(
            kwargs, cache, clientCountry, header)
        if len(geoip_results) >= minimum:
            if not ordered_mirrorlist:
                done = 1

    if not done:
        header, continent_results = do_continent(
            kwargs, cache, clientCountry, [], header)
        if len(geoip_results) + len(continent_results) >= minimum:
            done = 1

    if not done:
        header, global_results = do_global(
            kwargs, cache, clientCountry, header)

    def _random_shuffle(s):
        l = list(s)
        random.shuffle(l)
        return l

    def _ordered_netblocks(s):
        def ipy_len(t):
            (prefix, hostid) = t
            return IP(prefix).len()
        v4_netblocks = []
        v6_netblocks = []
        for (prefix, hostid) in s:
            ip = IP(prefix)
            if ip.version() == 4:
                v4_netblocks.append((prefix, hostid))
            elif ip.version() == 6:
                v6_netblocks.append((prefix, hostid))
        # mix up the order, as sort will preserve same-key ordering
        random.shuffle(v4_netblocks)
        v4_netblocks.sort(key=ipy_len)
        random.shuffle(v6_netblocks)
        v6_netblocks.sort(key=ipy_len)
        v4_netblocks = [t[1] for t in v4_netblocks]
        v6_netblocks = [t[1] for t in v6_netblocks]
        return v6_netblocks + v4_netblocks

    def whereismymirror(result_sets):
        return_string = 'None'
        allhosts = []
        found = False
        for (l,s,f) in result_sets:
            if len(l) > 0:
                allhosts.extend(f(l))
                if not found:
                    return_string = s
                    found = True

        allhosts = uniqueify(allhosts)
        return allhosts, return_string

    result_sets = [
        (location_results, "location", _random_shuffle),
        (netblock_results, "netblocks", _ordered_netblocks),
        (asn_results, "asn", _random_shuffle),
        (internet2_results, "I2", _random_shuffle),
        (country_results, "country", shuffle),
        (geoip_results, "geoip", shuffle),
        (continent_results, "continent", shuffle),
        (global_results, "global", shuffle),
        ]

    allhosts, where_string = whereismymirror(result_sets)
    try:
        ip_str = kwargs['IP'].strNormal()
    except:
        ip_str = 'Unknown IP'
    log_string = "mirrorlist: %s found its best mirror from %s" % (
        ip_str, where_string)
    syslogger.info(log_string)

    hosts_and_urls = append_path(
        allhosts, cache, file, pathIsDirectory=pathIsDirectory)

    protocols_trimmed = False
    if 'protocol' in kwargs and kwargs['protocol']:
        try:
            # Expecting a single string as value
            # of the parameter protocol.
            # Trying to convert it to a tuple for
            # the protocol trim function.
            try_protocols = (kwargs['protocol'],)
            hosts_and_urls = trim_to_preferred_protocols(
                    hosts_and_urls, try_protocols)
            protocols_trimmed = True
            header += 'protocol = %s ' % (kwargs['protocol'])
        except:
            pass

    if 'time' in kwargs:
        try:
            # Last code modifying the header. Let's enter a newline
            header += '\n# database creation time: %s' % (database['time'])
        except:
            pass

    if 'metalink' in kwargs and kwargs['metalink']:
        (resulttype, returncode, results)=metalink(
            cache, dir, file, hosts_and_urls)
        d = dict(
            message=None,
            resulttype=resulttype,
            returncode=returncode,
            results=results)
        return d

    else:
        if not protocols_trimmed:
            hosts_and_urls = trim_to_preferred_protocols(hosts_and_urls)
        d = dict(
            message=header,
            resulttype='mirrorlist',
            returncode=200,
            results=hosts_and_urls)
        return d


def setup_cache_tree(cache, field):
    tree = radix.Radix()
    for k, v in cache.items():
        node = tree.add(k.strNormal())
        node.data[field] = v
    return tree


def setup_netblocks(netblocks_file, asns_wanted=None):
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
                if asns_wanted is None or asn in asns_wanted:
                    node = tree.add(s[0])
                    node.data['asn'] = asn
            except:
                pass
        f.close()
    return tree


def read_caches():
    info = {}

    data = {}

    mirrorlist = mirrormanager_pb2.MirrorList()
    protobuf = False

    f = open(cachefile, 'rb')
    try:
        data = pickle.load(f)
    except pickle.UnpicklingError:
        # If it is not a pickle, then it probably is the
        # protobuf based format.
        f.seek(0)
        mirrorlist.ParseFromString(f.read())
        protobuf = True
        del(data)
        pass
    f.close()

    if protobuf:
        # This transforms the protobuf input back to the
        # same format as the pickle input.

        info['time'] = datetime.datetime.fromtimestamp(mirrorlist.Time)

        tmp = {}
        for i, item in enumerate(mirrorlist.HostAsnCache):
            if item.key not in tmp.keys():
                tmp[item.key] = []
            for v, value in enumerate(item.value):
                tmp[item.key].append(value)
        info['asn_host_cache'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.NetblockCountryCache):
            tmp[
                IP(item.key)] = item.value
        info['netblock_country_cache'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.LocationCache):
            if item.key not in tmp.keys():
                tmp[item.key] = []
            for v, value in enumerate(item.value):
                tmp[item.key].append(value)
        info['location_cache'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.HCUrlCache):
            tmp[item.key] = item.value
        info['hcurl_cache'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.FileDetailsCache):
            if item.directory not in tmp.keys():
                tmp[item.directory] = {}
            fdcf = item.FileDetailsCacheFiles
            for fd, file_details in enumerate(fdcf):
                tmp[item.directory][file_details.filename] = []
                details_list = file_details.FileDetails
                for v, value in enumerate(details_list):
                    fd = {}
                    fd['timestamp'] = value.TimeStamp
                    fd['size'] = value.Size
                    fd['sha1'] = value.SHA1
                    fd['md5'] = value.MD5
                    fd['sha256'] = value.SHA256
                    fd['sha512'] = value.SHA512
                    tmp[item.directory][file_details.filename].append(fd)
        info['file_details_cache'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.DisabledRepositoryCache):
            tmp[item.key] = item.value
        info['disabled_repositories'] = tmp
        tmp = {}
        for i, item in enumerate(mirrorlist.CountryContinentRedirectCache):
            tmp[item.key] = item.value
        info['country_continent_redirect_cache'] = tmp
        tmp = {}
        for i, item in enumerate(mirrorlist.RepositoryRedirectCache):
            tmp[item.key] = item.value
        info['repo_redirect'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.RepoArchToDirectoryName):
            tmp[
                (item.key.split('+')[0], item.key.split('+')[1])
            ] = item.value
        info['repo_arch_to_directoryname'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.HostMaxConnectionCache):
            tmp[item.key] = item.value
        info['host_max_connections_cache'] = tmp
        tmp = {}
        for i, item in enumerate(mirrorlist.HostCountryCache):
            tmp[item.key] = item.value
        info['host_country_cache'] = tmp
        tmp = {}
        for i, item in enumerate(mirrorlist.HostBandwidthCache):
            tmp[item.key] = item.value
        info['host_bandwidth_cache'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.HostNetblockCache):
            if IP(item.key) not in tmp.keys():
                tmp[IP(item.key)] = []
            for v, value in enumerate(item.value):
                tmp[IP(item.key)].append(value)
        info['host_netblock_cache'] = tmp

        tmp = {}
        for i, item in enumerate(mirrorlist.MirrorListCache):
            if item.directory not in tmp.keys():
                tmp[item.directory] = {}
            mc = tmp[item.directory]
            mc['subpath'] = item.Subpath
            mc['ordered_mirrorlist'] = item.OrderedMirrorList
            mc['global'] = set()
            for v, value in enumerate(item.Global):
                mc['global'].add(value)
            mc['byCountry'] = {}
            for c, country in enumerate(item.ByCountry):
                mc['byCountry'][country.key] = set()
                for v, value in enumerate(country.value):
                    mc['byCountry'][country.key].add(value)
            mc['byCountryInternet2'] = {}
            for c, country in enumerate(item.ByCountryInternet2):
                mc['byCountryInternet2'][country.key] = set()
                for v, value in enumerate(country.value):
                    mc['byCountryInternet2'][country.key].add(value)
            mc['byHostId'] = {}
            for i, id in enumerate(item.ByHostId):
                mc['byHostId'][id.key] = []
                for h, hcurl in enumerate(id.value):
                    mc['byHostId'][id.key].append(hcurl)
        info['mirrorlist_cache'] = tmp
        mirrorlist.Clear()

    else:
        if 'mirrorlist_cache' in data:
            info['mirrorlist_cache'] = data['mirrorlist_cache']
        if 'host_netblock_cache' in data:
            info['host_netblock_cache'] = data['host_netblock_cache']
        if 'host_country_allowed_cache' in data:
            info['host_country_allowed_cache'] = data[
                'host_country_allowed_cache']
        if 'repo_arch_to_directoryname' in data:
            info['repo_arch_to_directoryname'] = data[
                'repo_arch_to_directoryname']
        if 'repo_redirect_cache' in data:
            info['repo_redirect'] = data['repo_redirect_cache']
        if 'country_continent_redirect_cache' in data:
            info['country_continent_redirect_cache'] = data[
                'country_continent_redirect_cache']
        if 'disabled_repositories' in data:
            info['disabled_repositories'] = data['disabled_repositories']
        if 'host_bandwidth_cache' in data:
            info['host_bandwidth_cache'] = data['host_bandwidth_cache']
        if 'host_country_cache' in data:
            info['host_country_cache'] = data['host_country_cache']
        if 'file_details_cache' in data:
            info['file_details_cache'] = data['file_details_cache']
        if 'hcurl_cache' in data:
            info['hcurl_cache'] = data['hcurl_cache']
        if 'asn_host_cache' in data:
            info['asn_host_cache'] = data['asn_host_cache']
        if 'location_cache' in data:
            info['location_cache'] = data['location_cache']
        if 'netblock_country_cache' in data:
            info['netblock_country_cache'] = data['netblock_country_cache']
        if 'host_max_connections_cache' in data:
            info['host_max_connections_cache'] = data[
                'host_max_connections_cache']
        if 'time' in data:
            info['time'] = data['time']

    setup_continents(info)

    info['internet2_tree'] = setup_netblocks(internet2_netblocks_file)
    info['global_tree']    = setup_netblocks(global_netblocks_file, info['asn_host_cache'])
    # host_netblocks_tree key is a netblock, value is a list of host IDs
    info['host_netblocks_tree'] = setup_cache_tree(info['host_netblock_cache'], 'hosts')
    # netblock_country_tree key is a netblock, value is a single country string
    info['netblock_country_tree'] = setup_cache_tree(
        info['netblock_country_cache'], 'country')

    return info


def errordoc(metalink, message):
    if metalink:
        doc = metalink_failuredoc(message)
    else:
        doc = message
    return doc


class MirrorlistHandler(StreamRequestHandler):
    def handle(self):
        random.seed()
        try:
            # read size of incoming pickle
            readlen = 0
            size = ''
            while readlen < 10:
                size += self.rfile.read(10 - readlen).decode()
                readlen = len(size)
            size = int(size)
            print(size)

            # read the pickle
            readlen = 0
            p = b''
            while readlen < size:
                p += self.rfile.read(size - readlen)
                readlen = len(p)
            d = pickle.loads(p)
            self.connection.shutdown(socket.SHUT_RD)
        except:
            raise

        try:
            try:
                r = do_mirrorlist(d)
            except:
                raise
            message = r['message']
            results = r['results']
            resulttype = r['resulttype']
            returncode = r['returncode']
        except Exception as e:
            message=u'# Bad Request %s\n# %s' % (e, d)
            exception_msg = traceback.format_exc(e)
            sys.stderr.write(message+'\n')
            sys.stderr.write(exception_msg)
            sys.stderr.flush()
            returncode = 400
            results = []
            resulttype = 'mirrorlist'
            if d['metalink']:
                resulttype = 'metalink'
                results = errordoc(d['metalink'], message)

        try:
            p = pickle.dumps({
                'message':message,
                'resulttype':resulttype,
                'results':results,
                'returncode':returncode})
            self.connection.sendall(str(len(p)).encode().zfill(10))

            self.connection.sendall(p)
            self.connection.shutdown(socket.SHUT_WR)
        except:
            pass


def sighup_handler(signum, frame):
    global logfile
    if logfile is not None:
        name = logfile.name
        logfile.close()
        logfile = open(name, 'a')

    # put this in a separate thread so it doesn't block clients
    thread = threading.Thread(target=load_databases_and_caches)
    thread.daemon = False
    try:
        thread.start()
    except KeyError:
    # bug fix for handing an exception when unable to delete from
    #_limbo even though it's not in limbo
    # https://code.google.com/p/googleappengine/source/browse/trunk/python/google/appengine/dist27/threading.py?r=327
        pass


def sigterm_handler(signum, frame):
    global must_die
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if signum == signal.SIGTERM:
        must_die = True


class ThreadingUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 300
    def finish_request(self, request, client_address):
        BaseServer.finish_request(self, request, client_address)


def parse_args():
    global cachefile
    global socketfile
    global internet2_netblocks_file
    global global_netblocks_file
    global logfile
    global pidfile
    global minimum
    global country_continent_csv
    opts, args = getopt.getopt(
        sys.argv[1:], "c:i:g:p:s:dl:m:",
        [
            "cache", "internet2_netblocks", "global_netblocks",
            "pidfile", "socket", "log=", "minimum=", "cccsv="
        ]
    )
    for option, argument in opts:
        if option in ("-c", "--cache"):
            cachefile = argument
        if option in ("-i", "--internet2_netblocks"):
            internet2_netblocks_file = argument
        if option in ("-g", "--global_netblocks"):
            global_netblocks_file = argument
        if option in ("-s", "--socket"):
            socketfile = argument
        if option in ("-p", "--pidfile"):
            pidfile = argument
        if option == "--cccsv":
            country_continent_csv = argument
        if option in ("-l", "--log"):
            try:
                logfile = open(argument, 'a')
            except:
                logfile = None
        if option in ("-m", "--minimum"):
            minimum = int(argument)

    sys.stderr.write("Minimum mirrors is set to %d\n" % (minimum))
    sys.stderr.flush()


def open_geoip_databases():
    info = {'geoip': None }
    try:
        info['geoip'] = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-Country.mmdb')
    except:
        pass
    return info


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


def load_databases_and_caches(*args, **kwargs):
    global database
    global country_continents

    new_database = {
        'geoip': None,
        # key is strings in tuple (repo.prefix, arch)
        'mirrorlist_cache': {},
        # key is an IPy.IP structure, value is list of host ids
        'host_netblock_cache': {},
        # key is hostid, value is list of countries to allow
        'host_country_allowed_cache': {},
        'repo_arch_to_directoryname': {},
        # redirect from a repo with one name to a repo with another
        'repo_redirect': {},
        'country_continent_redirect_cache': {},
        'disabled_repositories': {},
        'host_bandwidth_cache': {},
        'host_country_cache': {},
        'host_max_connections_cache': {},
        'file_details_cache': {},
        'hcurl_cache': {},
        'asn_host_cache': {},
        'internet2_tree': radix.Radix(),
        'global_tree': radix.Radix(),
        'host_netblocks_tree': radix.Radix(),
        'netblock_country_tree': radix.Radix(),
        'location_cache': {},
        'netblock_country_cache': {}
        }
    sys.stderr.write("load_databases_and_caches...")
    sys.stderr.flush()
    new_database.update(open_geoip_databases())
    new_database.update(read_caches())
    sys.stderr.write("done.\n")
    sys.stderr.flush()
    # Update the entire in-memory structure at once
    database = new_database


def remove_pidfile(pidfile):
    os.unlink(pidfile)


def create_pidfile_dir(pidfile):
    piddir = os.path.dirname(pidfile)
    if not piddir:
        return
    try:
        os.makedirs(piddir, mode=0o755)
    except OSError as err:
        if err.errno == 17: # File exists
            pass
        else:
            raise
    except:
        raise


def write_pidfile(pidfile, pid):
    create_pidfile_dir(pidfile)
    f = open(pidfile, 'w')
    f.write(str(pid)+'\n')
    f.close()
    return 0


def manage_pidfile(pidfile):
    """returns 1 if another process is running that is named in pidfile,
    otherwise creates/writes pidfile and returns 0."""
    pid = os.getpid()
    try:
        f = open(pidfile, 'r')
    except IOError as err:
        if err.errno == 2: # No such file or directory
            return write_pidfile(pidfile, pid)
        return 1

    oldpid=f.read()
    f.close()

    # is the oldpid process still running?
    try:
        os.kill(int(oldpid), 0)
    except ValueError: # malformed oldpid
        return write_pidfile(pidfile, pid)
    except OSError as err:
        if err.errno == 3: # No such process
            return write_pidfile(pidfile, pid)
    return 1


def main():
    global logfile
    global pidfile
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    parse_args()
    manage_pidfile(pidfile)

    oldumask = os.umask(0)
    try:
        os.unlink(socketfile)
    except:
        pass

    load_databases_and_caches()
    signal.signal(signal.SIGHUP, sighup_handler)
    # restart interrupted syscalls like select
    signal.siginterrupt(signal.SIGHUP, False)
    ss = ThreadingUnixStreamServer(socketfile, MirrorlistHandler)

    while not must_die:
        try:
            ss.serve_forever()
        except select.error:
            pass

    try:
        os.unlink(socketfile)
    except:
        pass

    if logfile is not None:
        try:
            logfile.close()
        except:
            pass

    remove_pidfile(pidfile)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(-1)
