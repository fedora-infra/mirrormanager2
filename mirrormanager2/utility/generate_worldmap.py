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
@click.option("--verbose", is_flag=True, default=False, help="show more details")
def main(config, verbose):
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
            gir = None
            try:
                addrinfo = socket.getaddrinfo(hn, None)
                # Extract the IPv4 and IPv6 address from the tuples returned by
                # getaddrinfo.
                addresses = set()
                for family, socktype, proto, canonname, sockaddr in addrinfo:
                    # The GeoIP2 databases contain only information for IPv4 and
                    # IPv6 addresses. Therefore, other, unusual address families
                    # are ignored.
                    if family == socket.AF_INET:
                        address, port = sockaddr
                        addresses.add(address)
                    elif family == socket.AF_INET6:
                        address, port, flowinfo, scope_id = sockaddr
                        addresses.add(address)
                # Retrieve the city object for each address.
                cities = []
                for address in addresses:
                    try:
                        city = gi.city(address)
                    except geoip2.errors.AddressNotFoundError:
                        # If no city object was found for an IPv4 or IPv6
                        # address, the address is ignored.
                        pass
                    else:
                        # It seems that an empty city record is returned when no
                        # city was found. If no city has been found for an IPv4
                        # or IPv6 address, the address is ignored.
                        if city.city.name is not None:
                            cities.append(city)
                # If no city objects were found, the location of a host cannot
                # be determined.
                if not cities:
                    continue
                city_names = (city.city.name for city in cities)
                # Only the GeoIP2 Enterprise database has a confidence score for
                # each city record. Therefore, it seems best to use the most
                # frequently occuring city if a host has multiple addresses.
                city_name_counter = collections.Counter(city_names)
                # most_common(1) returns a list with one element that is tuple
                # that consists of the item and its count.
                most_common_city_name = city_name_counter.most_common(1)[0][0]
                # Find a city object for the most common city name. Any city
                # object should equivalent for a given city name.
                for city in cities:
                    if most_common_city_name == city.city.name:
                        gir = city
                        break
            except Exception:
                continue
            if gir is None:
                continue
            if gir.country.iso_code in embargoed_countries:
                click.echo(
                    f"WARNING: host {host.id} ({hostname}) seems to be from an embargoed "
                    f"country: {gir.country.iso_code}",
                    err=True,
                )
                continue
            host.latitude = gir.location.latitude
            host.longitude = gir.location.longitude
            tracking.add(host.id)
            if verbose:
                click.echo(f"{host.name} ({host.id}): {host.latitude} {host.longitude}")
        session.commit()
