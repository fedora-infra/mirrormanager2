"""
The purpose of this script is to download a BGP table of netblocks
and then write out a file matching those netblocks to ASNs (autonomous system
numbers).  ASNs are administrative numbers designated by IAANA which define a
kind of boundary for a set of routers.  For instance, MIT's ASN is 3; every
router within MIT's sphere of influence bears that ASN.  Every ISP has their
own, etc.


This script produces one of two netblocks files which gets read in by the
mirrorlist-server daemon and used as part of the larger mirror-matching logic
there.  When people query the mirrorlist, we can match their IP (potentially)
to an ASN to get them to a mirror that's closer to them than not.
"""

import bz2
import logging
import os
import re
from contextlib import contextmanager
from datetime import date, timedelta
from io import BytesIO
from shutil import copyfile
from tempfile import NamedTemporaryFile

import click
import mrtparse
import requests

from .common import setup_logging

# TODO: rich progress bar

GLOBAL_NETBLOCKS_URL = "http://ftp.routeviews.org/dnszones/rib.bz2"
IPV6_NETBLOCKS_URL = "http://archive.routeviews.org/route-views6/bgpdata/{year}.{month}/RIBS"
ROUTERS = ["ATLA", "CHIC", "HOUS", "KANS", "LOSA", "NEWY", "SALT", "SEAT", "WASH"]
INTERNET2_URL = "http://routes.net.internet2.edu/bgp/RIBS/{router}/{year}/{month}/{day}"
RIB_LINK_RE = re.compile(r'<a href="(rib.[0-9]+.[0-9]+.bz2)">')
EXCLUDED_LINES = [
    # This prefix appears repeatedly for multiple ASs, which is nuts.
    re.compile(r"2001::/32"),
    # For I2
    re.compile(r"Unknown"),
    re.compile(r"^0\.0/16"),
    re.compile(r"^10\.0\.0/16"),
    re.compile(r"^000:206f"),
]


logger = logging.getLogger(__name__)


def get_last_rib_url(url):
    url = url.rstrip("/")
    response = requests.get(f"{url}/?C=M;O=D")
    response.raise_for_status()
    rib_files = RIB_LINK_RE.findall(response.text)
    return f"{url}/{rib_files[0]}"


def _type_name(type_dict):
    return list(type_dict.values())[0]


def _get_as_value(table_entry):
    for path_attribute in table_entry["rib_entries"][0]["path_attributes"]:
        if _type_name(path_attribute["type"]) != "AS_PATH":
            continue
        for as_path in path_attribute["value"]:
            if _type_name(as_path["type"]) != "AS_SEQUENCE":
                continue
            return as_path["value"][-1]


def _parse_rib(content):
    lines = []
    for entry in mrtparse.Reader(content):
        if _type_name(entry.data["type"]) != "TABLE_DUMP_V2":
            continue
        if _type_name(entry.data["subtype"]) not in ["RIB_IPV4_UNICAST", "RIB_IPV6_UNICAST"]:
            continue
        try:
            as_value = _get_as_value(entry.data)
        except Exception:
            continue
        line = f"{entry.data['prefix']}/{entry.data['length']} {as_value}"
        # uniq
        if line in lines:
            continue
        # Remove excluded prefixes
        if any([ep.search(line) is not None for ep in EXCLUDED_LINES]):
            continue
        lines.append(line)
    return lines


def get_global_netblocks(local_file=None):
    if local_file:
        print(f"Using local global netblocks file: {local_file}")
        content_source = local_file
    else:
        print("Downloading global netblocks...")
        response = requests.get(GLOBAL_NETBLOCKS_URL)
        response.raise_for_status()
        content_source = BytesIO(response.content)

    with bz2.open(content_source) as content:
        return _parse_rib(content)


def get_ipv6_netblocks(local_file=None):
    if local_file:
        print(f"Using local IPv6 netblocks file: {local_file}")
        content_source = local_file
    else:
        print("Downloading IPv6 netblocks...")
        yesterday = date.today() - timedelta(days=1)
        url = IPV6_NETBLOCKS_URL.format(year=yesterday.year, month=yesterday.strftime("%m"))
        last_rib_url = get_last_rib_url(url)
        response = requests.get(last_rib_url)
        response.raise_for_status()
        content_source = BytesIO(response.content)

    with bz2.open(content_source) as content:
        return _parse_rib(content)


def get_i2_netblocks():
    yesterday = date.today() - timedelta(days=1)
    result = []
    for router in ROUTERS:
        url = INTERNET2_URL.format(
            router=router,
            year=yesterday.year,
            month=yesterday.strftime("%m"),
            day=yesterday.strftime("%d"),
        )
        last_rib_url = get_last_rib_url(url)
        response = requests.get(last_rib_url)
        response.raise_for_status()
        with open(response.content) as content:
            result.extend(_parse_rib(content))
    result.sort()
    return result


@contextmanager
def result_file(filename):
    with NamedTemporaryFile(prefix="mm2-netblocks-", suffix=".txt", mode="w+") as tmpfile:
        yield tmpfile
        tmpfile.flush()
        statinfo = os.stat(tmpfile.name)
        # do not overwrite if we have no result
        if statinfo.st_size == 0:
            raise click.ClickException("Unable to retrieve netblock list")
        copyfile(tmpfile.name, filename)


@click.group()
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
def main(debug):
    setup_logging(debug=debug)


@main.command("global")
@click.argument("output", type=click.Path())
@click.option(
    "--global-file",
    type=click.Path(exists=True),
    help="Use local global netblocks file instead of downloading",
)
@click.option(
    "--ipv6-file",
    type=click.Path(exists=True),
    help="Use local IPv6 netblocks file instead of downloading",
)
@click.option(
    "--disable-global", is_flag=True, default=False, help="Skip global netblocks processing"
)
@click.option("--disable-ipv6", is_flag=True, default=False, help="Skip IPv6 netblocks processing")
def global_netblocks(output, global_file, ipv6_file, disable_global, disable_ipv6):
    # Validate that at least one processing mode is enabled
    if disable_global and disable_ipv6:
        raise click.ClickException(
            "Cannot disable both global and IPv6 processing. At least one must be enabled."
        )

    # Show configuration summary
    print("=== Netblocks Processing Configuration ===")

    if disable_global:
        print("Global netblocks: DISABLED")
    elif global_file:
        print(f"Global netblocks: Using local file {global_file}")
    else:
        print(f"Global netblocks: Downloading from {GLOBAL_NETBLOCKS_URL}")

    if disable_ipv6:
        print("IPv6 netblocks: DISABLED")
    elif ipv6_file:
        print(f"IPv6 netblocks: Using local file {ipv6_file}")
    else:
        yesterday = date.today() - timedelta(days=1)
        url = IPV6_NETBLOCKS_URL.format(year=yesterday.year, month=yesterday.strftime("%m"))
        print(f"IPv6 netblocks: Downloading from {url}")

    print(f"Output file: {output}")
    print()

    with result_file(output) as output_file:
        # Build sources list based on disable flags
        sources = []
        if not disable_global:
            sources.append(("global", get_global_netblocks(global_file)))
        if not disable_ipv6:
            sources.append(("IPv6", get_ipv6_netblocks(ipv6_file)))

        for source_name, source_data in sources:
            print(f"Processing {source_name} netblocks...")
            count = 0
            for line in source_data:
                output_file.write(line)
                output_file.write("\n")
                count += 1
            print(f"Processed {count:,} {source_name} netblocks")

        print("Processing complete!")


@main.command()
@click.argument("output", type=click.Path())
def internet2(output):
    with result_file(output) as output_file:
        for line in get_i2_netblocks():
            output_file.write(line)
            output_file.write("\n")
