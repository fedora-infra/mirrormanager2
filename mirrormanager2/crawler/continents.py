import collections
import csv
import functools
import logging
import os
import socket
from functools import cache
from importlib import resources
from urllib.parse import urlparse

import geoip2

import mirrormanager2.lib

from .constants import CONTINENTS

logger = logging.getLogger(__name__)


class WrongContinent(Exception):
    pass


class EmbargoedCountry(Exception):
    def __init__(self, country):
        self.country = country


class BrokenBaseUrl(ValueError):
    pass


def filter_continents(asked):
    continents = []
    for continent in CONTINENTS:
        if f"^{continent}" in asked:
            continue
        if asked and continent not in asked:
            continue
        continents.append(continent)
    return continents


@functools.cache
def get_country_continents(session):
    country_continent_csv = resources.files("mirrormanager2.crawler").joinpath(
        "country_continent.csv"
    )
    new_country_continents = {}
    with country_continent_csv.open("r") as infile:
        reader = csv.reader(infile)
        new_country_continents = {rows[0]: rows[1] for rows in reader}
    for c in mirrormanager2.lib.get_country_continent_redirect(session):
        new_country_continents[c.country] = c.continent
    return new_country_continents


@cache
def get_geoip(base_dir):
    return geoip2.database.Reader(os.path.join(base_dir, "GeoLite2-Country.mmdb"))


def check_continent(config, options, session, categoryUrl):
    gi = get_geoip(config["GEOIP_BASE"])
    continents = filter_continents(options["continents"])
    country_continents = get_country_continents(session)
    # Before the first network access to the mirror let's
    # check if continent mode is enabled and verfiy if
    # the mirror is on the target continent.
    # The continent check takes the first URL of the first category
    # for the decision on which continent the mirror is.
    try:
        hostname = urlparse.urlsplit(categoryUrl)[1]
    except Exception as e:
        # Not being able the split the URL is strange.
        # Something is broken.
        raise BrokenBaseUrl() from e

    # The function urlsplit() does not remove ':' in case someone
    # specified a port. Only look at the first element before ':'
    hostname = hostname.split(":")[0]

    try:
        addrinfo = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        # Name resolution failed. This means
        # that the base URL is broken.
        raise BrokenBaseUrl() from e

    # Extract the IPv4 and IPv6 address from the tuples returned by getaddrinfo.
    addresses = set()
    for family, _socktype, _proto, _canonname, sockaddr in addrinfo:
        # The GeoIP2 databases contain only information for IPv4 and IPv6
        # addresses. Therefore, other, unusual address families are ignored.
        if family == socket.AF_INET:
            address, port = sockaddr
            addresses.add(address)
        elif family == socket.AF_INET6:
            address, port, flowinfo, scope_id = sockaddr
            addresses.add(address)
    # Retrieve the ISO 3166-1 code for each address.
    countries = []
    for address in addresses:
        try:
            country = gi.country(address)
        except geoip2.errors.AddressNotFoundError:
            # If no country object is found for an IPv4 or IPv6 address,
            # the address is ignored.
            pass
        else:
            iso_code = country.country.iso_code
            # If the ISO 3166-1 code is not available, the country cannot be
            # matched to continent. Therefore, the country object is ignored.
            if iso_code is not None:
                countries.append(iso_code)
    # The GeoIP2 databases are not perfect and fully accurate. Therefore,
    # multiple countries might be returned for hosts with multiple addresses. It
    # seems best to use the most frequently occuring country if a host has
    # multiple addresses.
    country_counter = collections.Counter(countries)
    if country_counter:
        # most_common(1) returns a list with one element that is tuple that
        # consists of the item and its count.
        country = country_counter.most_common(1)[0][0]
    else:
        # For hosts with no country in the GeoIP database
        # the default is 'US' as that is where most of
        # Fedora infrastructure systems are running
        country = "US"
    if country in config["EMBARGOED_COUNTRIES"]:
        raise EmbargoedCountry(country)
    if country_continents[country] in continents:
        return
    # And another return value. '8' is used for mirrors on
    # the wrong continent. The crawl should not be listed in
    # the database at all.
    raise WrongContinent
