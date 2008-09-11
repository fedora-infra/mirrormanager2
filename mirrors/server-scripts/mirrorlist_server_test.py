#!/usr/bin/python
#
# Copyright (c) 2007 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

import socket
import cPickle as pickle
from string import zfill, atoi

socketfile = '/var/run/mirrormanager/mirrorlist_server.sock'

def do_mirrorlist(d):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(socketfile)
    except:
        raise

    p = pickle.dumps(d)
    size = len(p)
    print "writing size %s to server" % size
    s.sendall(zfill('%s' % size, 10))

    # write the pickle
    print "writing the pickle"
    s.sendall(p)
    s.shutdown(socket.SHUT_WR)
    del p

    print "reading result pickle size back"
    readlen = 0
    resultsize = ''
    while readlen < 10:
        resultsize += s.recv(10 - readlen)
        readlen = len(resultsize)
    resultsize = atoi(resultsize)
    
    print "reading %s bytes of the results list" % resultsize
    readlen = 0
    p = ''
    while readlen < resultsize:
        p += s.recv(resultsize - readlen)
        readlen = len(p)
        
    s.shutdown(socket.SHUT_RD)
    results = pickle.loads(p)
    del p

    return results


# This takes 0.120-0.126 seconds, so should be done before any requests
import random

client_ip = "%s.%s.%s.%s" % (random.randint(0,255), random.randint(0,255), random.randint(0,255), random.randint(0,255))

d = {'repo':'fedora-9',
     'arch':'i386',
     'client_ip':client_ip}

print do_mirrorlist(d)

