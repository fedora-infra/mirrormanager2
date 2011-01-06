import os
import re
from mirrormanager.model import Category, HostCategory
import dns.zone
from dns.exception import DNSException
from dns.rdataclass import *
from dns.rdatatype import *

default_ttl = 3600
default_output_dir = '/var/lib/mirrormanager/dns'

def domainTemplateToName(domain, country):
    return re.sub(u'CC', country, domain)

def generateZoneFiles(directory):
    zones = {}

    for c in Category.select():
        if c.GeoDNSDomain is None: continue
        hcs = HostCategory.selectBy(category=c)
        hosts = [ hc.host for hc in hcs if hc.host.dnsCountryHost ]
        for h in hosts:
            if h.country in zones:
                z = zones[h.country]['zone']
            else:
                domainname = domainTemplateToName(c.GeoDNSDomain, h.country)
                z = dns.zone.Zone(domainname)
                zones[h.country] = {}
                zones[h.country]['zone'] = z
                zones[h.country]['name'] = domainname

            rdataset = z.find_rdataset('@', rdtype=CNAME, create=True)
            rdata = dns.rdtypes.ANY.CNAME.CNAME(IN, CNAME, h.name)
            rdataset.add(rdata, ttl=default_ttl)

    for country, z in zones.iteritems():
        z['zone'].to_file(os.path.join(directory, u'zone-' + z['name']))

def writeZoneFiles():
    output_dir = default_output_dir
    try:
        os.makedirs(output_dir)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise
    generateZoneFiles(output_dir)


__all__ = ['writeZoneFiles']
