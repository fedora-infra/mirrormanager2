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
import multiprocessing
import os
import queue
import re
import threading
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from datetime import date, timedelta
from shutil import copyfile
from tempfile import NamedTemporaryFile, TemporaryDirectory

import click
import mrtparse
import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .common import setup_logging

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
# How many parsed BGP entries between two progress updates.
PROGRESS_INTERVAL = 1000


logger = logging.getLogger(__name__)


def _download(url, destination, description):
    """Download url into destination, showing a progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get("content-length", 0))

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task(description, total=total_size or None)
        with open(destination, "wb") as downloaded:
            for chunk in response.iter_content(chunk_size=8192):
                downloaded.write(chunk)
                progress.update(task, advance=len(chunk))


def get_last_rib_url(url):
    url = url.rstrip("/")
    response = requests.get(f"{url}/?C=M;O=D")
    response.raise_for_status()
    rib_files = RIB_LINK_RE.findall(response.text)
    return f"{url}/{rib_files[0]}"


def _type_name(type_dict):
    return list(type_dict.values())[0]


def _get_as_value(table_entry):
    """Return the originating AS of a table entry, or None if it has none."""
    try:
        for path_attribute in table_entry["rib_entries"][0]["path_attributes"]:
            if _type_name(path_attribute["type"]) != "AS_PATH":
                continue
            for as_path in path_attribute["value"]:
                if _type_name(as_path["type"]) != "AS_SEQUENCE":
                    continue
                return as_path["value"][-1]
    except (KeyError, IndexError, TypeError):
        # Skip entries with an unexpected structure
        return None
    return None


def _parse_rib(content, report_progress=None):
    """
    Turn an open BGP RIB file into a sorted list of "<prefix>/<length> <ASN>" lines.

    If report_progress is given it is called with the number of entries read so far and
    the number of netblocks found so far, every PROGRESS_INTERVAL entries and once at
    the end.
    """
    lines = set()
    processed = 0

    for entry in mrtparse.Reader(content):
        processed += 1
        if report_progress is not None and processed % PROGRESS_INTERVAL == 0:
            report_progress(processed, len(lines))

        if _type_name(entry.data["type"]) != "TABLE_DUMP_V2":
            continue
        if _type_name(entry.data["subtype"]) not in ["RIB_IPV4_UNICAST", "RIB_IPV6_UNICAST"]:
            continue
        as_value = _get_as_value(entry.data)
        if as_value is None:
            continue
        line = f"{entry.data['prefix']}/{entry.data['length']} {as_value}"
        # Remove excluded prefixes
        if any([ep.search(line) is not None for ep in EXCLUDED_LINES]):
            continue
        # The set takes care of the uniq
        lines.add(line)

    if report_progress is not None:
        report_progress(processed, len(lines))

    return sorted(lines)


def _process_rib_file(path, name, progress_queue):
    """
    Parse a BGP RIB file and report the progress back over progress_queue.

    This runs in a worker process: parsing is CPU bound and the GIL would otherwise
    serialize the IPv4 and the IPv6 table.
    """
    counters = {"processed": 0, "found": 0}

    def report_progress(processed, found):
        counters.update(processed=processed, found=found)
        progress_queue.put({"type": "progress", "name": name, **counters})

    with bz2.open(path) as content:
        lines = _parse_rib(content, report_progress)

    progress_queue.put({"type": "complete", "name": name, **counters})
    return lines


def _monitor_progress(progress_queue, progress, tasks):
    """Update the progress bars from the messages the worker processes send."""
    while True:
        try:
            message = progress_queue.get(timeout=1)
        except queue.Empty:
            continue
        if message["type"] == "stop":
            break
        name = message["name"]
        description = f"{name} netblocks (found: {message['found']:,})"
        if message["type"] == "complete":
            description = f"{description} - COMPLETE"
        progress.update(tasks[name], completed=message["processed"], description=description)


def _download_global_netblocks(directory):
    """Download the global netblocks file and return its path."""
    path = os.path.join(directory, "global.bz2")
    _download(GLOBAL_NETBLOCKS_URL, path, "Downloading global netblocks")
    return path


def _download_ipv6_netblocks(directory):
    """Download the IPv6 netblocks file and return its path."""
    yesterday = date.today() - timedelta(days=1)
    url = IPV6_NETBLOCKS_URL.format(year=yesterday.year, month=yesterday.strftime("%m"))
    path = os.path.join(directory, "ipv6.bz2")
    _download(get_last_rib_url(url), path, "Downloading IPv6 netblocks")
    return path


def get_i2_netblocks():
    yesterday = date.today() - timedelta(days=1)
    result = []
    with TemporaryDirectory(prefix="mm2-netblocks-") as tmpdir:
        for router in ROUTERS:
            url = INTERNET2_URL.format(
                router=router,
                year=yesterday.year,
                month=yesterday.strftime("%m"),
                day=yesterday.strftime("%d"),
            )
            path = os.path.join(tmpdir, f"{router}.bz2")
            _download(get_last_rib_url(url), path, f"Downloading Internet2 netblocks ({router})")
            with bz2.open(path) as content:
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

    with result_file(output) as output_file, TemporaryDirectory(prefix="mm2-netblocks-") as tmpdir:
        # First make every enabled RIB file available locally.
        sources = []
        if not disable_global:
            sources.append(("global", global_file or _download_global_netblocks(tmpdir)))
        if not disable_ipv6:
            sources.append(("IPv6", ipv6_file or _download_ipv6_netblocks(tmpdir)))

        # Then parse them, one worker process per file.
        for name, _path in sources:
            print(f"Processing {name} netblocks...")

        with multiprocessing.Manager() as manager:
            progress_queue = manager.Queue()
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.completed]{task.completed:>7,} entries"),
            ) as progress:
                # The number of entries is only known once the file has been read.
                tasks = {
                    name: progress.add_task(f"{name} netblocks", total=None)
                    for name, _path in sources
                }
                monitor = threading.Thread(
                    target=_monitor_progress,
                    args=(progress_queue, progress, tasks),
                    daemon=True,
                )
                monitor.start()
                try:
                    with ProcessPoolExecutor(max_workers=len(sources)) as executor:
                        futures = [
                            executor.submit(_process_rib_file, path, name, progress_queue)
                            for name, path in sources
                        ]
                        # Keep the output in source order, not in completion order.
                        results = [future.result() for future in futures]
                finally:
                    progress_queue.put({"type": "stop"})
                    monitor.join(timeout=2)

        for (name, _path), netblocks in zip(sources, results):
            for line in netblocks:
                output_file.write(line)
                output_file.write("\n")
            print(f"Processed {len(netblocks):,} {name} netblocks")

        print("Processing complete!")


@main.command()
@click.argument("output", type=click.Path())
def internet2(output):
    with result_file(output) as output_file:
        for line in get_i2_netblocks():
            output_file.write(line)
            output_file.write("\n")
