#!/usr/bin/env python
#
# Copyright (c) 2014 Red Hat, Inc.
# Copyright (c) 2007-2013 Dell, Inc.
#  by Matt Domsch <Matt_Domsch@dell.com>
# Licensed under the MIT/X11 license

# Environment Variables setable via Apache SetEnv directive:
# mirrorlist_client.noreverseproxy
#  if set (to anything), do not look at X-Forwarded-For headers.  This
#  is used in environments that do not have a Reverse Proxy (HTTP
#  accelerator) in front of the application server running this WSGI,
#  to avoid looking "behind" the real client's own forward HTTP proxy.

import socket
import select
try:
    import cPickle as pickle
except ImportError:
    import pickle
from webob import Request, Response

socketfile = '/var/run/mirrormanager/mirrorlist_server.sock'
select_timeout = 60  # seconds
timeout = 5  # seconds


def get_mirrorlist(d):
    # any exceptions or timeouts raised here get handled by the caller
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(socketfile)

    p = pickle.dumps(d)
    del d
    size = len(p)
    s.sendall(str(size).zfill(10))

    # write the pickle
    s.sendall(p)
    s.shutdown(socket.SHUT_WR)
    del p

    # wait for other end to start writing
    rlist, wlist, xlist = select.select([s], [], [], select_timeout)
    if len(rlist) == 0:
        s.shutdown(socket.SHUT_RD)
        raise socket.timeout

    readlen = 0
    resultsize = ''
    while readlen < 10:
        resultsize += s.recv(10 - readlen)
        readlen = len(resultsize)
    resultsize = int(resultsize)

    readlen = 0
    p = ''
    while readlen < resultsize:
        p += s.recv(resultsize - readlen)
        readlen = len(p)
    results = pickle.loads(p)
    del p

    s.shutdown(socket.SHUT_RD)
    return results


def real_client_ip(xforwardedfor):
    """Only the last-most entry listed is the where the client
    connection to us came from, so that's the only one we can trust in
    any way."""
    return xforwardedfor.split(',')[-1].strip()


def request_setup(environ, request):
    fields = [
        'repo', 'arch', 'country', 'path', 'netblock', 'location',
        'version', 'cc', 'protocol', 'time'
    ]
    d = {}
    request_data = request.GET
    for f in fields:
        if f in request_data:
            d[f] = request_data[f].strip()
            # add back '+' that were converted to ' ' by util.FieldStorage
            if f == 'path':
                d[f] = d[f].replace(' ', '+')

    if 'ip' in request_data:
        client_ip = request_data['ip'].strip()
    elif 'X-Forwarded-For' in request.headers \
            and 'mirrorlist_client.noreverseproxy' not in environ:
        client_ip = real_client_ip(
            request.headers['X-Forwarded-For'].strip())
    else:
        client_ip = request.environ['REMOTE_ADDR']
    d['client_ip'] = client_ip

    # convert cc to country (for CentOS)
    if 'cc' in d and 'country' not in d:
        d['country'] = d['cc']
        del d['cc']

    # convert version=&repo=& to repo=<repo>-<version> (for CentOS)
    if 'version' in d and 'repo' in d:
        d['repo'] = "%s-%s" % (d['repo'], d['version'])
        del d['version']

    d['metalink'] = False
    scriptname = ''
    pathinfo = ''
    if 'SCRIPT_NAME' in request.environ:
        scriptname = request.environ['SCRIPT_NAME']
    if 'PATH_INFO' in request.environ:
        pathinfo = request.environ['PATH_INFO']
    if scriptname == '/metalink' or pathinfo == '/metalink':
        d['metalink'] = True

    for k, v in d.items():
        try:
            d[k] = unicode(v, 'utf8', 'replace')
        except:
            pass
    return d


def get_first_http_url(input):
    """ Only used for the redirect case. In the case
    a redirect has been requested only the first URL
    is returned starting with 'http'."""
    for hostid, url in input:
        for u in url:
            if u.startswith(u'http'):
                return u
    return None


def application(environ, start_response):
    request = Request(environ)
    response = Response()

    d = request_setup(environ, request)

    try:
        r = get_mirrorlist(d)
        message = r['message']
        resulttype = r['resulttype']
        results = r['results']
        # returncode = r['returncode']
    except:  # most likely socket.error, but we'll catch everything
        response.status_code = 503
        return response(environ, start_response)

    if resulttype == 'mirrorlist':
        # results look like [(hostid, [url, url]), ...]
        if 'redirect' in request.GET:
            if len(results) == 0:
                response.status_code = 404
            else:
                url = get_first_http_url(results)
                if url:
                    response.status_code = 302
                    response.headers['Location'] = str(url)
                else:
                    response.status_code = 404
            return response(environ, start_response)

        text = ""
        text += message + '\n'
        for (hostid, url) in results:
            text += url[0] + '\n'
        results = text
        response.headers['Content-Type'] = "text/plain"
    elif resulttype == 'metalink':
        # results are an XML document
        response.headers['Content-Type'] = "application/metalink+xml"
    else:
        response.headers['Content-Type'] = "text/plain"

    results = results.encode('utf-8')
    response.write(results)
    return response(environ, start_response)


if __name__ == '__main__':
    from wsgiref import simple_server
    httpd = simple_server.make_server('127.0.0.1', 8090, application)
    print('Serving on http://127.0.0.1:8090')
    httpd.serve_forever()
