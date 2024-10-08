# Copyright (c) 2007-2012 Dell, Inc. by Matt Domsch <Matt_Domsch@dell.com>
# Copyright (c) 2015,2018 Adrian Reber <adrian@lisas.de>
#
# Based on examples from python-GeoIP and python-basemap-examples
# Licensed under the GNU General Public License v2
# because it uses data from python-basemap-data which is GPL
# while the rest of MirrorManager is licensed MIT/X11


from urllib.parse import urlsplit

import click

from mirrormanager2.lib import geo, get_host_category_url, read_config
from mirrormanager2.lib.database import get_db_manager

from .common import config_option


@click.command()
@config_option
@click.option("--verbose", is_flag=True, default=False, help="show more details")
def main(config, verbose):
    config = read_config(config)
    gi = geo.get_geoip(config["GEOIP_BASE"], "City")
    db_manager = get_db_manager(config)
    with db_manager.Session() as session:
        embargoed_countries = set(x.upper() for x in config["EMBARGOED_COUNTRIES"])
        tracking = set()
        for hcurl in get_host_category_url(session):
            host = hcurl.host_category.host
            if host.private or host.site.private:
                continue
            hostname = urlsplit(hcurl.url)[1]
            if host.id in tracking:
                continue
            try:
                addresses = geo.get_host_addresses(hostname)
            except geo.HostUnreachable:
                click.echo(f"Unreachable host: {hostname}. Skipping.", err=True)
                continue

            city = geo.get_city(addresses, geoip_db=gi)
            if city is None:
                continue
            if city.country.iso_code in embargoed_countries:
                click.echo(
                    f"WARNING: host {host.id} ({hostname}) seems to be from an embargoed "
                    f"country: {city.country.iso_code}",
                    err=True,
                )
                continue
            host.latitude = city.location.latitude
            host.longitude = city.location.longitude
            tracking.add(host.id)
            if verbose:
                click.echo(f"{host.name} ({host.id}): {host.latitude} {host.longitude}")
        session.commit()
