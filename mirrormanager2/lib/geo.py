import collections
import socket

import geoip2


class HostUnreachable(Exception):
    pass


def get_host_addresses(hostname):
    """Get the IP addresses for a hostname"""
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise HostUnreachable(hostname) from e

    # Extract the IPv4 and IPv6 address from the tuples returned by getaddrinfo.
    addresses = set()
    for family, _socktype, _proto, _canonname, sockaddr in addrinfo:
        # The GeoIP2 databases contain only information for IPv4 and IPv6
        # addresses. Therefore, other, unusual address families are ignored.
        if family not in (socket.AF_INET, socket.AF_INET6):
            continue
        addresses.add(sockaddr[0])
    return addresses


def get_country(addresses, geoip_db):
    """Retrieve the ISO 3166-1 code for each address."""
    countries = []
    for address in addresses:
        try:
            country = geoip_db.country(address)
        except geoip2.errors.AddressNotFoundError:
            # If no country object is found for an IPv4 or IPv6 address,
            # the address is ignored.
            continue
        iso_code = country.country.iso_code
        if iso_code is None:
            # If the ISO 3166-1 code is not available, the country cannot be
            # matched to continent. Therefore, the country object is ignored.
            continue
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
    return country


def get_city(addresses, geoip_db):
    """Retrieve the city object for each address."""
    cities = []
    for address in addresses:
        try:
            city = geoip_db.city(address)
        except geoip2.errors.AddressNotFoundError:
            # If no city object was found for an IPv4 or IPv6
            # address, the address is ignored.
            continue
        # It seems that an empty city record is returned when no
        # city was found. If no city has been found for an IPv4
        # or IPv6 address, the address is ignored.
        if city.city.name is None:
            continue
        cities.append(city)
    # If no city objects were found, the location of a host cannot
    # be determined.
    if not cities:
        return None
    city_names = [city.city.name for city in cities]
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
            return city
