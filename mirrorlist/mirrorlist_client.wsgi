#!/usr/bin/python
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
import cPickle as pickle
from string import zfill, atoi, strip, replace
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
    s.sendall(zfill('%s' % size, 10))

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
    resultsize = atoi(resultsize)

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
        'version', 'cc'
    ]
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
    elif 'X-Forwarded-For' in request.headers \
            and 'mirrorlist_client.noreverseproxy' not in environ:
        client_ip = real_client_ip(
            strip(request.headers['X-Forwarded-For']))
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

    for k, v in d.iteritems():
        try:
            d[k] = unicode(v, 'utf8', 'replace')
        except:
            pass
    return d


def keep_only_http_results(input):
    output = []
    for hostid, url in input:
        if url.startswith(u'http'):
            output.append((hostid, url))
    return output


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
        # results look like [(hostid, url), ...]
        if 'redirect' in request.GET:
            if len(results) == 0:
                response.status_code = 404
            else:
                results = keep_only_http_results(results)
                if len(results):
                    (hostid, url) = results[0]
                    response.status_code = 302
                    response.headers['Location'] = str(url)
                else:
                    response.status_code = 404
            return response(environ, start_response)

        text = ""
        text += message + '\n'
        for (hostid, url) in results:
            text += url + '\n'
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


if __name__ == '__main__':  # pragma: no cover
    import sys
    import os

    # Run the unit tests. You can also perform coverage analysis by running:
    # coverage run mirrorlist_client.wsgi --test && coverage html
    if '--test' in sys.argv:
        # This requires the mirrorlist_server.py to be running
        if not os.path.exists(socketfile):
            print("You must run the mirrorlist_server.py first")

        import webtest
        import subprocess

        app = webtest.TestApp(application)
        resp = app.get('/metalink', {
            'repo': 'updates-testing-f20', 'arch': 'x86_64'
            }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)
        proc = subprocess.Popen(['xmllint', '--noout', '-'],
                                stdin=subprocess.PIPE)
        proc.stdin.write(resp.body)
        out, err = proc.communicate()
        assert proc.returncode == 0, proc.returncode

        # Test the mirrorlist
        resp = app.get('/mirrorlist', {
            'repo': 'updates-testing-f20',
            'arch': 'x86_64',
            }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)
        assert '# repo = updates-testing-f20 arch = x86_64 country = global' \
            in resp, resp

        # Test mirrorlist redirection
        resp = app.get('/mirrorlist', {
            'repo': 'updates-testing-f20',
            'arch': 'x86_64',
            'redirect': '1'
        }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=302)

        # Test X-Forwarded-For
        resp = app.get('/mirrorlist', {
            'repo': 'updates-testing-f20', 'arch': 'x86_64'
            }, headers={'X-Forwarded-For': '127.0.0.1'},
            extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)

        # version + repo (for centos)
        resp = app.get('/mirrorlist', {
            'version': 'f20', 'repo': 'updates-testing', 'arch': 'x86_64'
            }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)

        # cc instead of country
        resp = app.get('/mirrorlist', {
            'repo': 'updates-testing-f20', 'arch': 'x86_64', 'cc': 'US'
            }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)

        # Specify an ip
        resp = app.get('/mirrorlist', {
            'repo': 'updates-testing-f20',
            'arch': 'x86_64',
            'ip': '10.10.10.10',
            }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)

    else:
        from wsgiref import simple_server
        httpd = simple_server.make_server('127.0.0.1', 8090, application)
        print('Serving on http://127.0.0.1:8090')
        httpd.serve_forever()
