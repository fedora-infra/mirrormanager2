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


@click.command()
@config_option
def main(config):
    config = mirrormanager2.lib.read_config(config)
    gi = geoip2.database.Reader(os.path.join(config["GEOIP_BASE"], "GeoLite2-City.mmdb"))
    db_manager = get_db_manager(config)
    with db_manager.Session() as session:
        embargoed_countries = set(x.upper() for x in config["EMBARGOED_COUNTRIES"])
        tracking = set()
        for hcurl in mirrormanager2.lib.get_host_category_url(session):
            host = hcurl.host_category.host
            if host.private or host.site.private:
                continue
            hostname = urlsplit(hcurl.url)[1]
            if host.id in tracking:
                continue
            try:
                ip = socket.gethostbyname(hostname)
                gir = gi.city(ip)
            except Exception:
                continue
            if gir is None:
                continue
            if gir.country.iso_code in embargoed_countries:
                print(
                    f"WARNING: host {host.id} ({hostname}) seems to be from an embargoed "
                    f"country: {gir.country.iso_code}"
                )
                continue
            host.latitude = gir.location.latitude
            host.longitude = gir.location.longitude
            tracking.add(host.id)
        session.commit()
