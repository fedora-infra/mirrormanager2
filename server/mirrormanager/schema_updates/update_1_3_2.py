from mirrormanager.model import Host
from sqlobject import IntCol, BoolCol
from mirrormanager.mirrorlist import name_to_ips
import copy

from IPy import IP
import string
import dns.resolver
from urlparse import urlsplit
asnresolver = None

def setup_asn_resolver():
    result = []
    records = dns.resolver.query('routeviews.org', 'NS')
    for r in records:
        ips = name_to_ips(str(r))
        for ip in ips:
            result.append(str(ip))
    global asnresolver
    asnresolver = copy.copy(dns.resolver.get_default_resolver())
    asnresolver.nameserver = result

def update_host_table():
    rc = False
    try:
        Host.sqlmeta.delColumn('asn', changeSchema=True)
        Host.sqlmeta.delColumn('asn_clients', changeSchema=True)
    except:
        return True
    try:
        Host.asn = Host.sqlmeta.addColumn(IntCol(name='asn', default=None), changeSchema=True)
        Host.asn_clients = Host.sqlmeta.addColumn(BoolCol(name='asn_clients', default=True), changeSchema=True)
        rc = True
    except:
        raise
    return rc

def txtrecords(name):
    records=[]
    try:
        records = asnresolver.query(name, 'TXT')
        return records
    except:
        pass
    return records


def ip_to_asn(ip):
    asn = None
    if ip.version() == 6:
        return asn
    reversename = ip.reverseName()
    reversename = string.replace(reversename, 'in-addr.arpa', 'asn.routeviews.org')
    try:
        records= txtrecords(reversename)
    except:
        return asn

    for t in records:
        try:
            asn = int(t.strings[0])
            return asn
        except:
            pass
    return asn

def hostname_to_asn(hostname):
    asn = None
    ips = name_to_ips(hostname)
    for ip in ips:
        asn = ip_to_asn(ip)
        if asn is not None:
            return asn
    return asn

def set_host_asn(h):
    for hc in h.categories:
        for hcurl in hc.urls:
            scheme, netloc, path, query, fragment = urlsplit(hcurl.url)
            asn = hostname_to_asn(netloc)
            if asn is not None:
                print "Host %s ASN %d" % (h.name, asn)
                h.asn = asn
                h.asn_clients = True
                h.sync()
                return

def initialize_host_table():
    setup_asn_resolver()
    for h in Host.select():
        h.asn = None
        h.asn_clients = False
        h.sync()
    for h in Host.select():
        if h.is_active() and not h.is_private():
            set_host_asn(h)

def update():
    default_resolver = dns.resolver.get_default_resolver()
    default_resolver.lifetime=default_resolver.timeout
    rc = update_host_table()
    if rc:
        initialize_host_table()
