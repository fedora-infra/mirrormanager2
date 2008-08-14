#!/usr/bin/python
#
# Copyright (c) 2007 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

import socket
import cPickle as pickle
from string import zfill, atoi, strip, replace
from paste.wsgiwrappers import *


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

def request_setup(request):
    fields = ['repo', 'arch', 'country', 'path', 'netblock']
    d = {}
    request_data = request.GET
    for f in fields:
        if f in request_data:
            d[f] = strip(request_data[f])
            # add back '+' that were converted to ' ' by util.FieldStorage
            if f == 'path':
                d[f] = replace(d[f], ' ', '+')

    if 'ip' in request_data:
        client_ip = strip(request_data['ip'])
    elif 'X-Forwarded-For' in request.headers:
        client_ip = real_client_ip(strip(request.headers['X-Forwarded-For']))
    else:
        client_ip = request.environ['REMOTE_ADDR']
    d['client_ip'] = client_ip

    d['metalink'] = False
    fname = request.environ['PATH_INFO']
    if fname == '/metalink':
        d['metalink'] = True
    return d


def application(environ, start_response):
    request = WSGIRequest(environ)
    response = WSGIResponse()

    d = request_setup(request)

    try:
        r = get_mirrorlist(d)
        message=r['message']
        resulttype=r['resulttype']
        results = r['results']
        returncode = r['returncode']
    except: # most likely socket.error, but we'll catch everything
        response.status_code=503
        return response(environ, start_response)


    if resulttype == 'mirrorlist':
        # results look like [(hostid, url), ...]
        if 'redirect' in request.GET:
            if len(results) == 0:
                response.status_code=404
                return response(environ, start_response)
            else: 
                (hostid, url) = results[0]
                response.status_code=302
                response.headers['Location'] = str(url)
                return response(environ, start_response)

        text = ""
        text += message + '\n'
        for (hostid, url) in results:
            text += url + '\n'
        results = text
        response.headers['Content-Type'] = "text/html"
    elif resulttype == 'metalink':
        # results are an XML document
        response.headers['Content-Type'] = "application/metalink+xml"
    else:
        response.headers['Content-Type'] = "text/html"

    response.write(results)
    return response(environ, start_response)


if __name__ == '__main__':
    from paste import httpserver
    httpserver.serve(app, host='127.0.0.1', port='8080')
