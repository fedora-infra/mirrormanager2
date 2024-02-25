# Copyright (c) 2007-2012 Dell, Inc. by Matt Domsch <Matt_Domsch@dell.com>
# Copyright (c) 2015,2018 Adrian Reber <adrian@lisas.de>
#
# Based on examples from python-GeoIP and python-basemap-examples
# Licensed under the GNU General Public License v2
# because it uses data from python-basemap-data which is GPL
# while the rest of MirrorManager is licensed MIT/X11


import os
import socket
from urllib.parse import urlsplit

import click
import geoip2.database

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager

from .common import config_option


def uniq(input):
    seen = set()
    seen_add = seen.add
    return [x for x in input if not (x in seen or seen_add(x))]


def lookup_host_locations(config, gi):
    db_manager = get_db_manager(config)
    results = []
    with db_manager.Session() as session:
        embargoed_countries = set(x.upper() for x in config["EMBARGOED_COUNTRIES"])
        tracking = []
        for hcurl in mirrormanager2.lib.get_host_category_url(session):
            if hcurl.host_category.host.private or hcurl.host_category.host.site.private:
                continue
            hostname = urlsplit(hcurl.url)[1]
            if hostname in tracking:
                continue
            try:
                ip = socket.gethostbyname(hostname)
                gir = gi.city(ip)
            except Exception:
                continue
            try:
                name = hcurl.host_category.host.site.name
            except Exception:
                name = "N/A"
            if gir is not None:
                if gir.country.iso_code in embargoed_countries:
                    print("skipping " + hostname)
                    continue
                t = (hostname, gir.country.iso_code, gir.location.latitude, gir.location.longitude)
                print("{} {} {} {}".format(*t))
                results.append([t, name])
                tracking.append(hostname)
    return results


def doit(output, config):
    gi = geoip2.database.Reader(os.path.join(config["GEOIP_BASE"], "GeoLite2-City.mmdb"))
    results = lookup_host_locations(config, gi)
    if not os.path.isdir(output):
        os.makedirs(output)
    marker_url = config.get("APPLICATION_ROOT", "/") + "static/map/f-dot.png"
    with open(os.path.join(output, "mirrors_location.txt"), "w", encoding="utf-8-sig") as fd:
        fd.write("lat\tlon\ttitle\tdescription\ticonSize\ticonOffset\ticon\n")
        for t in results:
            hostname = t[0][0]
            lat = t[0][2]
            lon = t[0][3]
            fd.write(
                f"{lat}\t{lon}\t<a href='http://{hostname}/' rel='noopener noreferrer' "
                f"target='_blank'>{hostname}</a>"
                f"\t{t[1]}\t21,25\t-10,-25\t{marker_url}\n"
            )


@click.command()
@config_option
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    required=True,
    help="write output to DIR",
)
def main(config, output):
    config = mirrormanager2.lib.read_config(config)
    doit(output, config)
