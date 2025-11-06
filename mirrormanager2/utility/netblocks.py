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
import concurrent.futures
import logging
import multiprocessing
import os
import queue
import re
import threading
from contextlib import contextmanager
from datetime import date, timedelta
from io import BytesIO
from shutil import copyfile
from tempfile import NamedTemporaryFile

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

# Progress indication implemented with rich download progress bars and processing counters

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


def _download_with_progress(url, description="Downloading"):
    """Download a file with rich progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Get total file size
    total_size = int(response.headers.get("content-length", 0))

    if total_size == 0:
        print(f"{description}: {url} (size unknown)")
        return response.content

    # Set up rich progress bar
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=None,  # Use default console
    ) as progress:
        # Add download task
        task = progress.add_task(f"{description}", total=total_size)

        chunks = []
        chunk_size = 8192

        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                chunks.append(chunk)
                progress.update(task, advance=len(chunk))

    return b"".join(chunks)


def get_last_rib_url(url):
    url = url.rstrip("/")
    response = requests.get(f"{url}/?C=M;O=D")
    response.raise_for_status()
    rib_files = RIB_LINK_RE.findall(response.text)
    return f"{url}/{rib_files[0]}"


def _type_name(type_dict):
    return list(type_dict.values())[0]


def _get_as_value(table_entry):
    try:
        # Check if required structure exists
        if "rib_entries" not in table_entry:
            return None
        if not table_entry["rib_entries"]:
            return None
        if "path_attributes" not in table_entry["rib_entries"][0]:
            return None

        for path_attribute in table_entry["rib_entries"][0]["path_attributes"]:
            if _type_name(path_attribute["type"]) != "AS_PATH":
                continue
            for as_path in path_attribute["value"]:
                if _type_name(as_path["type"]) != "AS_SEQUENCE":
                    continue
                return as_path["value"][-1]
    except (KeyError, IndexError, TypeError):
        # Handle any unexpected BGP entry structure gracefully
        return None
    return None


def _process_netblocks_worker(content_bytes, description, excluded_patterns, progress_queue):
    """
    Self-contained worker function for processing netblocks in a separate process.
    This avoids GIL limitations by using true multiprocessing.
    Uses progress_queue to communicate progress back to main process.
    """
    import bz2
    import re
    from io import BytesIO

    import mrtparse

    def _type_name_local(type_dict):
        return list(type_dict.values())[0]

    def _get_as_value_local(table_entry):
        try:
            if "rib_entries" not in table_entry:
                return None
            if not table_entry["rib_entries"]:
                return None
            if "path_attributes" not in table_entry["rib_entries"][0]:
                return None

            for path_attribute in table_entry["rib_entries"][0]["path_attributes"]:
                if _type_name_local(path_attribute["type"]) != "AS_PATH":
                    continue
                for as_path in path_attribute["value"]:
                    if _type_name_local(as_path["type"]) != "AS_SEQUENCE":
                        continue
                    return as_path["value"][-1]
        except (KeyError, IndexError, TypeError):
            return None
        return None

    # Compile regex patterns locally
    excluded_regexes = [re.compile(pattern) for pattern in excluded_patterns]

    # Send start signal
    progress_queue.put({"task": description, "type": "start"})

    lines = set()
    processed = 0

    with bz2.open(BytesIO(content_bytes)) as content:
        for entry in mrtparse.Reader(content):
            processed += 1

            # Send progress updates every 1000 entries (more frequent for smoother progress)
            if processed % 1000 == 0:
                progress_queue.put(
                    {
                        "task": description,
                        "type": "progress",
                        "processed": processed,
                        "found": len(lines),
                    }
                )

            if _type_name_local(entry.data["type"]) != "TABLE_DUMP_V2":
                continue
            if _type_name_local(entry.data["subtype"]) not in [
                "RIB_IPV4_UNICAST",
                "RIB_IPV6_UNICAST",
            ]:
                continue
            if entry.data["prefix"] == "101.96.103.0":
                progress_queue.put(
                    {"task": description, "type": "debug", "message": f"Found debug entry: {entry}"}
                )
            as_value = _get_as_value_local(entry.data)
            if as_value is None:
                continue  # Skip entries with malformed or missing AS information
            line = f"{entry.data['prefix']}/{entry.data['length']} {as_value}"

            # Check exclusions first (cheaper than set lookup for excluded items)
            if any([ep.search(line) is not None for ep in excluded_regexes]):
                continue

            lines.add(line)  # O(1) duplicate detection with set

    # Send completion signal
    progress_queue.put(
        {"task": description, "type": "complete", "processed": processed, "found": len(lines)}
    )

    return sorted(lines)  # Return sorted list for consistent output


def _parse_rib(content):
    """Simple sequential BGP processing for non-parallel use cases."""
    lines = set()
    processed = 0

    for entry in mrtparse.Reader(content):
        processed += 1

        if _type_name(entry.data["type"]) != "TABLE_DUMP_V2":
            continue
        if _type_name(entry.data["subtype"]) not in ["RIB_IPV4_UNICAST", "RIB_IPV6_UNICAST"]:
            continue
        as_value = _get_as_value(entry.data)
        if as_value is None:
            continue
        line = f"{entry.data['prefix']}/{entry.data['length']} {as_value}"

        if any([ep.search(line) is not None for ep in EXCLUDED_LINES]):
            continue

        lines.add(line)

    return sorted(lines)


def _monitor_processing_progress(progress_queue, progress_display, tasks):
    """Monitor progress queue and update rich progress bars."""
    try:
        while True:
            try:
                message = progress_queue.get(timeout=1)
                msg_type = message["type"]

                if msg_type == "stop":
                    # Signal to stop monitoring
                    break
                elif msg_type == "start":
                    # Task started - progress bar already created
                    pass
                elif msg_type == "progress":
                    task_name = message["task"]
                    processed = message["processed"]
                    found = message["found"]
                    # Update progress bar (we use processed as the current value)
                    progress_display.update(
                        tasks[task_name],
                        completed=processed,
                        description=f"{task_name} (found: {found:,})",
                    )
                elif msg_type == "debug":
                    # Print debug messages
                    progress_display.console.print(f"[yellow]DEBUG[/yellow] {message['message']}")
                elif msg_type == "complete":
                    task_name = message["task"]
                    processed = message["processed"]
                    found = message["found"]
                    # Mark task as completed
                    progress_display.update(
                        tasks[task_name],
                        completed=processed,
                        description=f"{task_name} (found: {found:,}) - COMPLETE",
                    )
            except queue.Empty:
                # Check if all tasks are complete by trying to get without blocking
                continue
    except Exception as e:
        progress_display.console.print(f"[red]Progress monitor error: {e}[/red]")


def _download_global_netblocks():
    """Download global netblocks file and return raw content."""
    return _download_with_progress(GLOBAL_NETBLOCKS_URL, "Downloading global netblocks")


def _download_ipv6_netblocks():
    """Download IPv6 netblocks file and return raw content."""
    yesterday = date.today() - timedelta(days=1)
    url = IPV6_NETBLOCKS_URL.format(year=yesterday.year, month=yesterday.strftime("%m"))
    last_rib_url = get_last_rib_url(url)
    return _download_with_progress(last_rib_url, "Downloading IPv6 netblocks")


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
        content_bytes = _download_with_progress(
            last_rib_url, f"Downloading Internet2 netblocks ({router})"
        )
        with bz2.open(BytesIO(content_bytes)) as content:
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
def global_netblocks(output):
    with result_file(output) as output_file:
        # Phase 1: Download both files sequentially
        print("=== Phase 1: Downloading files ===")
        print("Downloading global netblocks...")
        global_content = _download_global_netblocks()
        print("Downloading IPv6 netblocks...")
        ipv6_content = _download_ipv6_netblocks()

        # Phase 2: Process both files in parallel using separate processes (avoids GIL)
        print("\n=== Phase 2: Processing files in parallel ===")

        # Convert EXCLUDED_LINES to string patterns for serialization
        excluded_patterns = [pattern.pattern for pattern in EXCLUDED_LINES]

        # Create progress queue for multiprocessing communication using Manager
        with multiprocessing.Manager() as manager:
            progress_queue = manager.Queue()

            # Set up rich progress display (no percentage since total is unknown)
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.completed]{task.completed:>7,} entries"),
                console=None,
            ) as progress:
                # Create progress tasks (we don't know total size, so use None)
                global_task = progress.add_task("global netblocks", total=None)
                ipv6_task = progress.add_task("IPv6 netblocks", total=None)

                tasks = {"global netblocks": global_task, "IPv6 netblocks": ipv6_task}

                # Start progress monitoring thread
                monitor_thread = threading.Thread(
                    target=_monitor_processing_progress,
                    args=(progress_queue, progress, tasks),
                    daemon=True,
                )
                monitor_thread.start()

                with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
                    global_future = executor.submit(
                        _process_netblocks_worker,
                        global_content,
                        "global netblocks",
                        excluded_patterns,
                        progress_queue,
                    )
                    ipv6_future = executor.submit(
                        _process_netblocks_worker,
                        ipv6_content,
                        "IPv6 netblocks",
                        excluded_patterns,
                        progress_queue,
                    )

                    # Collect results as they complete
                    for future in concurrent.futures.as_completed([global_future, ipv6_future]):
                        netblocks = future.result()
                        progress.console.print(
                            f"[green]Writing {len(netblocks):,} netblocks to output...[/green]"
                        )
                        for line in netblocks:
                            output_file.write(line)
                            output_file.write("\n")

                # Stop progress monitoring
                progress_queue.put({"type": "stop"})
                monitor_thread.join(timeout=1)


@main.command()
@click.argument("output", type=click.Path())
def internet2(output):
    with result_file(output) as output_file:
        for line in get_i2_netblocks():
            output_file.write(line)
            output_file.write("\n")
