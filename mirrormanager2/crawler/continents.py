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
        hostname = socket.gethostbyname(hostname)
    except Exception as e:
        # Name resolution failed. This means
        # that the base URL is broken.
        raise BrokenBaseUrl() from e

    country = gi.country(hostname).country.iso_code
    if not country:
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
