# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

from __future__ import print_function

import datetime
import time
import os
import hashlib
try:
    import cPickle as pickle
except ImportError:
    import pickle

from operator import itemgetter

from IPy import IP
import pprint
import dns.resolver

import mirrormanager2.lib
import mirrormanager2.lib.mirrormanager_pb2 as mm_pb2


global_caches = dict(
    # key is directoryname
    mirrorlist_cache={},
    # key is strings in tuple (repo.prefix, arch)
    repo_arch_to_directoryname={},
    # key is an IPy.IP structure, value is list of host ids
    host_netblock_cache={},
    # key is hostid, value is list of countries to allow
    host_country_allowed_cache={},
    host_country_cache={},
    host_bandwidth_cache={},
    host_asn_cache={},
)

data = dict()

def parent_dir(path):
    return os.path.dirname(path)


def append_value_to_cache(cache, key, value):
    if key not in cache:
        cache[key] = [value]
    else:
        cache[key].append(value)
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
            s = hashlib.sha1(pp.pformat(c).encode('utf-8')).hexdigest()
            if s in matches:
                mc[d][subcache] = matches[s]
            else:
                matches[s] = c
    return mc


def query_directory_exclusive_host(session):
    table = mirrormanager2.lib.get_directory_exclusive_host(session)
    cache = {}
    for (dname, hostid) in table:
        if dname not in cache:
            cache[dname] = set([hostid])
        else:
            cache[dname].add(hostid)
    return cache


def populate_directory_cache(session):
    global global_caches
    result = mirrormanager2.lib.query_directories(session)

    directory_exclusive_hosts = query_directory_exclusive_host(session)

    def setup_directory_repo_cache(session):
        cache = {}
        for r in mirrormanager2.lib.get_repositories(session):
            if r.directory and r.version and r.arch:
                append_value_to_cache(cache, r.directory.id, r)
        return cache

    def setup_version_ordered_mirrorlist_cache(session):
        cache = {}
        for v in mirrormanager2.lib.get_versions(session):
            cache[v.id] = v.ordered_mirrorlist
        return cache

    def setup_category_topdir_cache(session):
        cache = {}
        for c in mirrormanager2.lib.get_categories(session):
            cache[c.id] = len(c.topdir.name) + 1  # include trailing /
        return cache

    directory_repo_cache = setup_directory_repo_cache(session)
    cat_dirs = mirrormanager2.lib.get_category_directory(session)
    directory_category_cache = {}
    for catdir in cat_dirs:
        append_value_to_cache(
            directory_category_cache, catdir.directory_id, catdir.category_id)
    version_ordered_mirrorlist_cache = setup_version_ordered_mirrorlist_cache(
        session)
    category_topdir_cache = setup_category_topdir_cache(session)

    cache = {}
    for (directory_id, directoryname, hostid, country, hcurl,
            siteprivate, hostprivate, i2, i2_clients) in result:
        if directoryname in directory_exclusive_hosts and \
                hostid not in directory_exclusive_hosts[directoryname]:
            continue

        if directoryname not in cache:
            cache[directoryname] = {
                'global': set(),
                'byCountry': {},
                'byHostId': {},
                'ordered_mirrorlist': True,
                'byCountryInternet2': {}
            }

            repos = directory_repo_cache.get(directory_id)

            if repos:
                for repo in repos:
                    if repo is not None \
                            and repo.arch is not None \
                            and repo.prefix:
                        global_caches['repo_arch_to_directoryname'][
                            (repo.prefix, repo.arch.name)] = directoryname
                        # WARNING - this is a query # fixme use cache
                        cache[directoryname][
                            'ordered_mirrorlist'
                        ] = repo.version.ordered_mirrorlist

            numcats = len(directory_category_cache.get(directory_id, []))
            if numcats == 0:
                # no category, so we can't know a mirror host's URLs.
                # nothing to add.
                continue
            elif numcats >= 1:
                # any of them will do, so just look at the first one
                category_id = directory_category_cache[directory_id][0]

            cache[directoryname]['subpath'] = directoryname[
                category_topdir_cache[category_id]:]
            del repos

        if country is not None:
            country = country.upper()

        if not siteprivate and not hostprivate:
            add_host_to_set(cache[directoryname]['global'], hostid)

            if country is not None:
                if country not in cache[directoryname]['byCountry']:
                    cache[directoryname]['byCountry'][country] = set()
                add_host_to_set(
                    cache[directoryname]['byCountry'][country], hostid)

        if country is not None and i2 and \
                ((not siteprivate and not hostprivate) or i2_clients):
            if country not in cache[directoryname]['byCountryInternet2']:
                cache[directoryname]['byCountryInternet2'][country] = set()
            add_host_to_set(
                cache[directoryname]['byCountryInternet2'][country], hostid)

        append_value_to_cache(cache[directoryname]['byHostId'], hostid, hcurl)

    global_caches['mirrorlist_cache'] = shrink(cache)


def name_to_ips(name):
    result = []
    recordtypes = ('A', 'AAAA')
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
        cache[host.id] = [
            c.country.upper()
            for c in list(host.countries_allowed)
        ]
    return cache


def populate_host_max_connections_cache(cache, host):
    cache[host.id] = host.max_connections
    return cache


def populate_host_bandwidth_cache(cache, host):
    try:
        i = int(host.bandwidth_int)
        if i < 1:
            i = 1
        elif i > 100000:
            i = 100000  # max bandwidth 100Gb
        cache[host.id] = i
    except:
        cache[host.id] = 1

    return cache


def populate_host_country_cache(cache, host):
    cache[host.id] = host.country
    return cache


def populate_host_asn_cache(cache, host):
    if not host.asn_clients:
        return cache

    if host.asn is not None:
        append_value_to_cache(cache, host.asn, host.id)

    for peer_asn in list(host.peer_asns):
        append_value_to_cache(cache, peer_asn.asn, host.id)
    return cache


def repository_redirect_cache(session):
    cache = {}
    for r in mirrormanager2.lib.get_reporedirect(session):
        cache[r.from_repo] = r.to_repo
    return cache


def country_continent_redirect_cache(session):
    cache = {}
    for c in mirrormanager2.lib.get_country_continent_redirect(session):
        cache[c.country] = c.continent
    return cache


def disabled_repository_cache(session):
    cache = {}
    for r in mirrormanager2.lib.get_repositories(session):
        if r.disabled:
            cache[r.prefix] = True
    return cache


def file_details_cache(session):
    # cache{directoryname}{filename}[{details}]
    cache = {}
    # materialize this select to avoid making hundreds of thousands of queries
    for d in mirrormanager2.lib.get_directories(session):
        if len(d.fileDetails) > 0:
            cache[d.name] = {}
            for fd in list(d.fileDetails):
                details = dict(
                    timestamp=fd.timestamp,
                    sha1=fd.sha1,
                    md5=fd.md5,
                    sha256=fd.sha256,
                    sha512=fd.sha512,
                    size=fd.size)
                append_value_to_cache(cache[d.name], fd.filename, details)

    for dir in cache.keys():
        for file in cache[dir].keys():
            if len(cache[dir][file]) > 1:
                cache[dir][file] = sorted(
                    cache[dir][file],
                    key=itemgetter('timestamp'),
                    reverse=True)

    return cache


def hcurl_cache(session):
    cache = {}
    for hcurl in mirrormanager2.lib.get_host_category_url(session):
        cache[hcurl.id] = hcurl.url
    return cache


def location_cache(session):
    cache = {}
    for location in mirrormanager2.lib.get_locations(session):
        # This does not work - location.hosts does not exist
        cache[location.name] = [host.id for host in list(location.hosts)]
    return cache


def netblock_country_cache(session):
    cache = {}
    for n in mirrormanager2.lib.get_netblock_country(session):
        ip = None
        try:
            ip = IP(n.netblock)
        except:
            continue
        # guaranteed to be unique by database constraints
        cache[ip] = (n.country)

    return cache


def populate_host_caches(session):
    n = dict()
    ca = dict()
    b = dict()
    cc = dict()
    a = dict()
    mc = dict()

    for host in list(mirrormanager2.lib.get_hosts(session)):
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


def populate_all_caches(session):
    global data
    populate_host_caches(session)
    populate_directory_cache(session)
    data = {
        'mirrorlist_cache': global_caches['mirrorlist_cache'],
        'host_netblock_cache': global_caches['host_netblock_cache'],
        'host_country_allowed_cache': global_caches['host_country_allowed_cache'],
        'host_bandwidth_cache': global_caches['host_bandwidth_cache'],
        'host_country_cache': global_caches['host_country_cache'],
        'host_max_connections_cache': global_caches['host_max_connections_cache'],
        # yeah I misnamed this
        'asn_host_cache': global_caches['host_asn_cache'],
        'repo_arch_to_directoryname': global_caches['repo_arch_to_directoryname'],
        'repo_redirect_cache': repository_redirect_cache(session),
        'country_continent_redirect_cache': country_continent_redirect_cache(session),
        'disabled_repositories': disabled_repository_cache(session),
        'file_details_cache': file_details_cache(session),
        'hcurl_cache': hcurl_cache(session),
        'location_cache': location_cache(session),
        'netblock_country_cache': netblock_country_cache(session),
        'time': datetime.datetime.utcnow(),
    }


def dump_caches(session, filename="", protobuf_file=""):
    ''' This function writes the previously collected
    information (via populate_all_caches()) to a file.
    The output format can be a Python pickle or Protobuf.
    The reason to also offer Protobuf is to be independent
    of Python's pickle format which does not always work
    with different versions of Python and used libraries.'''

    if filename != "":
        try:
            f = open(filename, 'wb')
            pickle.dump(data, f)
            f.close()
            # print('Pickle generated at %s' % filename)
        except Exception as err:
            print('Error generating the pickle (%s): %s' % (
                filename, err))
            pass

    if protobuf_file != "":
        mirrorlist = mm_pb2.MirrorList()
        mirrorlist.Time = int(time.mktime(data['time'].timetuple()))
        for key in data['netblock_country_cache']:
            item = mm_pb2.StringStringMap()
            item.key = key.strNormal()
            item.value = data['netblock_country_cache'][key]
            n = mirrorlist.NetblockCountryCache.add()
            n.CopyFrom(item)

        for key in data['location_cache']:
            item = mm_pb2.StringRepeatedIntMap()
            item.key = key
            for value in data['location_cache'][key]:
                item.value.append(value)
            n = mirrorlist.LocationCache.add()
            n.CopyFrom(item)

        for key in data['hcurl_cache']:
            item = mm_pb2.IntStringMap()
            item.key = key
            item.value = data['hcurl_cache'][key]
            n = mirrorlist.HCUrlCache.add()
            n.CopyFrom(item)

        for key in data['asn_host_cache']:
            item = mm_pb2.IntRepeatedIntMap()
            item.key = key
            for value in data['asn_host_cache'][key]:
                item.value.append(value)
            n = mirrorlist.HostAsnCache.add()
            n.CopyFrom(item)

        for directory in data['file_details_cache']:
            fdcd = mm_pb2.FileDetailsCacheDirectoryType()
            fdcd.directory = directory
            for file_name in data['file_details_cache'][directory]:
                fdcf = mm_pb2.FileDetailsCacheFilesType()
                fdcf.filename = file_name
                for d in data['file_details_cache'][directory][file_name]:
                    fd = mm_pb2.FileDetailsType()
                    fd.TimeStamp = d['timestamp']
                    fd.Size = d['size']
                    if d['sha1']:
                        fd.SHA1 = d['sha1']
                    if d['md5']:
                        fd.MD5 = d['md5']
                    if d['sha256']:
                        fd.SHA256 = d['sha256']
                    if d['sha512']:
                        fd.SHA512 = d['sha512']
                    n = fdcf.FileDetails.add()
                    n.CopyFrom(fd)
                n = fdcd.FileDetailsCacheFiles.add()
                n.CopyFrom(fdcf)
            n = mirrorlist.FileDetailsCache.add()
            n.CopyFrom(fdcd)

        for key in data['disabled_repositories']:
            item = mm_pb2.StringBoolMap()
            item.key = key
            item.value = data['disabled_repositories'][key]
            n = mirrorlist.DisabledRepositoryCache.add()
            n.CopyFrom(item)

        for key in data['country_continent_redirect_cache']:
            item = mm_pb2.StringStringMap()
            item.key = key
            item.value = data['country_continent_redirect_cache'][key]
            n = mirrorlist.CountryContinentRedirectCache.add()
            n.CopyFrom(item)

        for key in data['repo_redirect_cache']:
            item = mm_pb2.StringStringMap()
            item.key = key
            item.value = data['repo_redirect_cache'][key]
            n = mirrorlist.RepositoryRedirectCache.add()
            n.CopyFrom(item)

        for key in data['repo_arch_to_directoryname']:
            item = mm_pb2.StringStringMap()
            item.key = key[0] + '+' + key[1]
            item.value = data['repo_arch_to_directoryname'][key]
            n = mirrorlist.RepoArchToDirectoryName.add()
            n.CopyFrom(item)

        for key in data['host_max_connections_cache']:
            item = mm_pb2.IntIntMap()
            item.key = key
            item.value = data['host_max_connections_cache'][key]
            n = mirrorlist.HostMaxConnectionCache.add()
            n.CopyFrom(item)

        for key in data['host_country_cache']:
            item = mm_pb2.IntStringMap()
            item.key = key
            item.value = data['host_country_cache'][key]
            n = mirrorlist.HostCountryCache.add()
            n.CopyFrom(item)

        for key in data['host_bandwidth_cache']:
            item = mm_pb2.IntIntMap()
            item.key = key
            item.value = data['host_bandwidth_cache'][key]
            n = mirrorlist.HostBandwidthCache.add()
            n.CopyFrom(item)

        for key in data['host_country_allowed_cache']:
            item = mm_pb2.IntRepeatedStringMap()
            item.key = key
            for value in data['host_country_allowed_cache'][key]:
                item.value.append(value)
            n = mirrorlist.HostCountryAllowedCache.add()
            n.CopyFrom(item)

        for key in data['host_netblock_cache']:
            item = mm_pb2.StringRepeatedIntMap()
            item.key = key.strNormal()
            for value in data['host_netblock_cache'][key]:
                item.value.append(value)
            n = mirrorlist.HostNetblockCache.add()
            n.CopyFrom(item)

        for directory in data['mirrorlist_cache']:
            mlc = mm_pb2.MirrorListCacheType()
            mlc.directory = directory
            for key in data['mirrorlist_cache'][directory]:
                if key == 'global':
                    for i in data['mirrorlist_cache'][directory][key]:
                        mlc.Global.append(i)
                if key == 'subpath':
                    mlc.Subpath = data[
                        'mirrorlist_cache'
                    ][directory][key]
                if key == 'ordered_mirrorlist':
                    mlc.OrderedMirrorList = data[
                        'mirrorlist_cache'
                    ][directory][key]
                if key == 'byCountry':
                    countries = data['mirrorlist_cache'][directory][key]
                    for country in countries:
                        item = mm_pb2.StringRepeatedIntMap()
                        item.key = country
                        ids = countries[country]
                        for i in ids:
                            item.value.append(i)
                        n = mlc.ByCountry.add()
                        n.CopyFrom(item)
                if key == 'byCountryInternet2':
                    countries = data['mirrorlist_cache'][directory][key]
                    for country in countries:
                        item = mm_pb2.StringRepeatedIntMap()
                        item.key = country
                        ids = countries[country]
                        for i in ids:
                            item.value.append(i)
                        n = mlc.ByCountryInternet2.add()
                        n.CopyFrom(item)
                if key == 'byHostId':
                    ids = data['mirrorlist_cache'][directory][key]
                    for id in ids:
                        item = mm_pb2.IntRepeatedIntMap()
                        item.key = id
                        hcurls = ids[id]
                        for i in hcurls:
                            item.value.append(i)
                        n = mlc.ByHostId.add()
                        n.CopyFrom(item)
            n = mirrorlist.MirrorListCache.add()
            n.CopyFrom(mlc)

        try:
            f = open(protobuf_file, 'wb')
            f.write(mirrorlist.SerializeToString())
            f.close()
        except Exception as err:
            print('Error writing %s: %s' % (filename, err))
            pass
