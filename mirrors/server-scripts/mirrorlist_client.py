#!/usr/bin/python
#
# Copyright (c) 2007 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

import socket
import cPickle as pickle
from string import zfill, atoi
from random import randint
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

def drop_null_hostids(results):
    return [ url for hostid, url in results if hostid is not None ]

def do_redirect(req, results):
    # interesting, we shouldn't have to str() this, but apparently we do.
    util.redirect(req, str(random.choice(results)))


def request_setup(req, request_data):
    fields = ['repo', 'arch', 'country', 'path', 'netblock']
    d = {}
    for f in fields:
        if f in request_data:
            d[f] = request_data[f]

     client_ip = req.get_remote_host()
     if kwargs.has_key('ip'):
         client_ip = kwargs['ip']
     else:
         if req.headers_in.has_key('X-Forwarded-For'):
             client_ip = real_client_ip(req.headers_in['X-Forwarded-For'])
     d['client_ip'] = client_ip
     return d


def handler(req):
    request_data = util.FieldStorage(req)
    d = request_setup(req, request_data)

    try:
        results = get_mirrorlist(d)
    except: # most likely socket.error, but we'll catch everything
        return apache.HTTP_SERVICE_UNAVAILABLE
        
    if d.has_key('redirect'):
        urls = drop_null_hostids(results)
        if len(urls) == 0:
            return apache.HTTP_NOT_FOUND
        else:
            do_redirect(req, urls)
            # this raises an exception so we're done now.
        
    req.content_type = "text/plain"
    result = ""
    for row in results:
        result += row[1] + '\n'
        
    req.write(result)
    return apache.OK
