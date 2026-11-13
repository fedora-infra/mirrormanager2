import csv
import functools
import logging
from importlib import resources
from urllib.parse import urlsplit

from mirrormanager2.lib import geo, get_country_continent_redirect

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
    excluded = {continent[1:] for continent in asked if continent.startswith("^")}
    included = {continent for continent in asked if not continent.startswith("^")}
    return [
        continent
        for continent in CONTINENTS
        if continent not in excluded and (not included or continent in included)
    ]


@functools.cache
def get_country_continents(session):
    country_continent_csv = resources.files("mirrormanager2.crawler").joinpath(
        "country_continent.csv"
    )
    new_country_continents = {}
    with country_continent_csv.open("r") as infile:
        reader = csv.reader(infile)
        new_country_continents = {rows[0]: rows[1] for rows in reader}
    for c in get_country_continent_redirect(session):
        new_country_continents[c.country] = c.continent
    return new_country_continents


def check_continent(config, options, session, categoryUrl):
    gi = geo.get_geoip(config["GEOIP_BASE"], "Country")
    continents = filter_continents(options["continents"])
    country_continents = get_country_continents(session)
    # Before the first network access to the mirror let's
    # check if continent mode is enabled and verfiy if
    # the mirror is on the target continent.
    # The continent check takes the first URL of the first category
    # for the decision on which continent the mirror is.
    try:
        hostname = urlsplit(categoryUrl).hostname
    except ValueError as e:
        raise BrokenBaseUrl() from e
    if not hostname:
        raise BrokenBaseUrl()

    try:
        addresses = geo.get_host_addresses(hostname)
    except geo.HostUnreachable as e:
        # Name resolution failed. This means
        # that the base URL is broken.
        raise BrokenBaseUrl() from e

    country = geo.get_country(addresses, geoip_db=gi)
    if country in config["EMBARGOED_COUNTRIES"]:
        raise EmbargoedCountry(country)
    if country_continents[country] in continents:
        return
    raise WrongContinent
