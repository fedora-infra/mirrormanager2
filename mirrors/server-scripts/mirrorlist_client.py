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



def do_redirect(req, results):
    # interesting, we shouldn't have to str() this, but apparently we do.
    # the results list is in priority order, sublists randomized, so we can choose
    # the first entry
    (hostid, url) = results[0]
    util.redirect(req, str(url))


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
        message=r['message']
        resulttype=r['resulttype']
        results = r['results']
        returncode = r['returncode']
    except: # most likely socket.error, but we'll catch everything
        return apache.HTTP_SERVICE_UNAVAILABLE

    if returncode == 500:
        req.status = apache.HTTP_INTERNAL_SERVER_ERROR

    if returncode == 404:
        req.status = apache.HTTP_NOT_FOUND

    if resulttype == 'mirrorlist':
        # results look like [(hostid, url), ...]
        if request_data.has_key('redirect'):
            if len(results) == 0:
                return apache.HTTP_NOT_FOUND
            else:
                do_redirect(req, results)
                # this raises an exception so we're done now.

        text = ""
        text += message + '\n'
        for (hostid, url) in results:
            text += url + '\n'
        results = text
        req.content_type = "text/plain"
    elif resulttype == 'metalink':
        # results are an XML document
        req.content_type = "application/metalink+xml"
    else:
        req.content_type = "text/html"

    req.write(results)
    return apache.OK
