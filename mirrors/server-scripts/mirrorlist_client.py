#!/usr/bin/python
#
# Copyright (c) 2007 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

import socket
import cPickle as pickle
from string import zfill, atoi, strip, replace
from mod_python import util, apache

socketfile = '/tmp/mirrormanager_mirrorlist_server.sock'

def get_mirrorlist(d):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(socketfile)
    except:
        raise

    p = pickle.dumps(d)
    del d
    size = len(p)
    s.sendall(zfill('%s' % size, 10))

    # write the pickle
    s.sendall(p)
    s.shutdown(socket.SHUT_WR)
    del p

    readlen = 0
    resultsize = ''
    while readlen < 10:
        resultsize += s.recv(10 - readlen)
        readlen = len(resultsize)
    resultsize = atoi(resultsize)
    
    readlen = 0
    p = ''
    while readlen < resultsize:
        p += s.recv(resultsize - readlen)
        readlen = len(p)
        
    s.shutdown(socket.SHUT_RD)
    results = pickle.loads(p)
    del p

    return results

def real_client_ip(xforwardedfor):
    """Only the last-most entry listed is the where the client
    connection to us came from, so that's the only one we can trust in
    any way."""
    return xforwardedfor.split(',')[-1].strip()

def trim_to_preferred_protocols(input):
    """ remove all but http and ftp URLs,
    and if both http and ftp are offered,
    leave only http"""
    hosts = {}
    result = []
    for v in input:
        (hostid, hcurl) = v
        if hostid not in hosts:
            hosts[hostid] = {'https': None, 'http': None, 'ftp': None}
        if hcurl.startswith('https:'):
            hosts[hostid]['https'] = v
        elif hcurl.startswith('http:'):
            hosts[hostid]['http'] = v
        elif hcurl.startswith('ftp:'):
            hosts[hostid]['ftp'] = v
            
    for (hostid, hcurl) in input:
        if hosts[hostid]['https'] is not None:
            result.append(hosts[hostid]['https'])
        elif hosts[hostid]['http'] is not None:
            result.append(hosts[hostid]['http'])
        elif hosts[hostid]['ftp'] is not None:
            result.append(hosts[hostid]['ftp'])
            
    result = uniquify(result)
    return result


def drop_null_hostids(results):
    return [ url for hostid, url in results if hostid is not None ]

def do_redirect(req, results):
    # interesting, we shouldn't have to str() this, but apparently we do.
    # the results list is in priority order, sublists randomized, so we can choose
    # the first entry
    util.redirect(req, str(results[0]))


def request_setup(req, request_data):
    fields = ['repo', 'arch', 'country', 'path', 'netblock']
    d = {}
    for f in fields:
        if request_data.has_key(f):
            d[f] = strip(request_data[f])
            # add back '+' that were converted to ' ' by util.FieldStorage
            if f == 'path':
                d[f] = replace(d[f], ' ', '+')

    if request_data.has_key('ip'):
        client_ip = strip(request_data['ip'])
    elif req.headers_in.has_key('X-Forwarded-For'):
        client_ip = real_client_ip(strip(req.headers_in['X-Forwarded-For']))
    else:
        client_ip = req.get_remote_host()
    d['client_ip'] = client_ip

    d['metalink'] = False
    fname = req.parsed_uri[apache.URI_PATH]
    if fname == '/metalink':
        d['metalink'] = True
    return d


def handler(req):
    request_data = util.FieldStorage(req)
    d = request_setup(req, request_data)

    try:
        r = get_mirrorlist(d)
        resulttype=r['resulttype']
        results = r['results']
        returncode = r['returncode']
    except: # most likely socket.error, but we'll catch everything
        return apache.HTTP_SERVICE_UNAVAILABLE

    if returncode == 500:
        req.status = apache.HTTP_INTERNAL_SERVER_ERROR

    if resulttype == 'mirrorlist':
        results = trim_to_preferred_protocols(results)
        if request_data.has_key('redirect'):
            urls = drop_null_hostids(results)
            if len(urls) == 0:
                return apache.HTTP_NOT_FOUND
            else:
                do_redirect(req, urls)
                # this raises an exception so we're done now.

        req.content_type = "text/plain"
        result = ""
        for (hostid, hcurl) in results:
            result += hcurl + '\n'

        req.write(result)
        return apache.OK
    else:
        req.content_type = "application/metalink+xml"
        req.write(results)
        return returncode
