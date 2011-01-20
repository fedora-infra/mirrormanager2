import os
import re
import errno
import IPy
import dns.zone
import dns.name
import dns.rdtypes.IN.A, dns.rdtypes.IN.AAAA 
from dns.exception import DNSException
from dns.rdataclass import *
from dns.rdatatype import *
from mirrormanager.model import Category, HostCategory
from mirrormanager.mirrorlist import name_to_ips

default_ttl = 600
default_output_dir = '/var/lib/mirrormanager/dns'

def domainTemplateToName(domain, country):
    return re.sub(u'CC', country, domain)

def generateZoneFile(directory):
    for c in Category.select():
        z = dns.zone.Zone(dns.name.from_text(''))
        if c.GeoDNSDomain is None: continue
        hosts = [ hc.host for hc in c.hostCategories if hc.host.dnsCountryHost ]
        for h in hosts:
            domainname = domainTemplateToName(c.GeoDNSDomain, h.country)
            n = dns.name.from_text(domainname)

            try:
                ips = [IPy.IP(h.name)]
            except ValueError:
                ips = name_to_ips(h.name)
            except:
                continue
          
            for ip in ips:
                if ip.version() == 4:
                    rdatasetA    = z.find_rdataset(n, rdtype=A, create=True)
                    rdata = dns.rdtypes.IN.A.A(IN, A, ip.strNormal())
                    rdatasetA.add(rdata, ttl=default_ttl)
                elif ip.version() == 6:
                    rdatasetAAAA = z.find_rdataset(n, rdtype=AAAA, create=True)
                    rdata = dns.rdtypes.IN.AAAA.AAAA(IN, AAAA, ip.strNormal())
                    rdatasetAAAA.add(rdata, ttl=default_ttl)
                else:
                    continue

        z.to_file(os.path.join(directory, u'zone-' + c.GeoDNSDomain))

def writeZoneFiles(output_dir = default_output_dir):
    try:
        os.makedirs(output_dir)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise
    generateZoneFile(output_dir)


__all__ = ['writeZoneFiles']
