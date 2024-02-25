import logging
import os
import time
from collections import defaultdict
from datetime import datetime

import click
from rich.console import Console
from rich.progress import Progress

from mirrormanager2.lib import get_categories, get_category_by_name, get_mirrors, model, read_config
from mirrormanager2.lib.database import get_db_manager

from .constants import CONTINENTS
from .crawler import PropagationResult, worker
from .fedora import get_current_versions
from .log import setup_logging
from .threads import run_in_threadpool
from .ui import report_crawl, report_propagation

logger = logging.getLogger(__name__)

DEFAULT_THREAD_COUNT = min(100, os.cpu_count() * 20)


def validate_continents(ctx, param, value):
    value = [c.upper() for c in value]
    for item in value:
        cont = item.lstrip("^")
        if cont not in CONTINENTS:
            raise click.BadParameter(
                f"Unknown continent {cont}. Known continents: {', '.join(CONTINENTS)}"
            )
    return value


@click.group()
@click.option(
    "-c",
    "--config",
    envvar="MM2_CONFIG",
    default="/etc/mirrormanager/mirrormanager2.cfg",
    help="Configuration file to use",
    show_default=True,
)
@click.option(
    "--include-private",
    is_flag=True,
    default=False,
    help="Include hosts marked 'private' in the crawl",
)
@click.option(
    "--category",
    "categories",
    multiple=True,
    help="Category to scan (default=all), can be repeated",
)
@click.option(
    "-t",
    "--threads",
    type=int,
    default=DEFAULT_THREAD_COUNT,
    help="max threads to start in parallel",
    show_default=True,
)
@click.option(
    "--timeout-minutes",
    "global_timeout",
    type=int,
    default=120,
    callback=lambda ctx, param, value: value * 60,
    help="global timeout, in minutes",
    show_default=True,
)
@click.option(
    "--host-timeout",
    "host_timeout",
    type=int,
    default=30,
    help="host timeout, in seconds",
    show_default=True,
)
@click.option(
    "--startid",
    type=int,
    metavar="ID",
    default=0,
    help="Start crawling at host ID",
    show_default=True,
)
@click.option(
    "--stopid",
    type=int,
    metavar="ID",
    default=0,
    help="Stop crawling before host ID (default=no limit)",
)
@click.option(
    "-f",
    "--fraction",
    default="1:1",
    help="""Specify which part of the mirror range should be returned:
1:1 = all mirrors, 1:2 = the first half of the mirrors,
2:3 = the middle third of the mirrors""",
    show_default=True,
)
@click.option(
    "--disable-fedmsg",
    "fedmsg",
    is_flag=True,
    default=True,
    help="Disable fedora-messaging notifications at the beginning and end of crawl",
)
@click.option(
    "--continent",
    "continents",
    multiple=True,
    callback=validate_continents,
    help="Limit crawling by continent. Exclude by prefixing with'^'",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    default=False,
    help="enable printing of debug-level messages",
)
@click.pass_context
def main(ctx, config, debug, categories, startid, stopid, fraction, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj["console"] = Console()

    setup_logging(debug, ctx.obj["console"])
    ctx.obj["options"] = ctx.params
    config = read_config(config)
    ctx.obj["config"] = config
    db_manager = get_db_manager(config)
    with db_manager.Session() as session:
        category_ids = []
        for category_name in categories:
            category = get_category_by_name(session, category_name)
            if category is None:
                available_categories = "".join(c.name for c in get_categories(session))
                raise click.BadOptionUsage(
                    "--category",
                    f"Category {category_name} does not exist. "
                    f"Available categories: {available_categories}",
                )
            category_ids.append(category.id)
        # Get *all* of the mirrors
        hosts = get_mirrors(
            session,
            private=False,
            order_by_crawl_duration=True,
            admin_active=True,
            user_active=True,
            site_private=False,
            site_user_active=True,
            site_admin_active=True,
            category_ids=category_ids or None,
        )

        # Limit our host list down to only the ones we really want to crawl
        if fraction and fraction != "1:1":
            if startid or stopid:
                raise click.BadOptionUsage(
                    "--fraction", "Cannot use --fraction with --startid or --stopid"
                )
            host_ids = [host.id for host in hosts]
            host_ids.sort()
            slices = int(fraction.split(":")[1])
            part = int(fraction.split(":")[0])
            start_index = (part - 1) * int(len(host_ids) / slices)
            stop_index = int(len(host_ids) / slices) * part

            if slices == part:
                # Final part
                startid = host_ids[start_index]
            else:
                startid = host_ids[start_index]
                stopid = host_ids[stop_index]

        ctx.obj["host_ids"] = [
            host.id for host in hosts if (host.id >= startid and (not stopid or host.id < stopid))
        ]

    # Before we do work, chdir to /var/tmp/.  mirrormanager1 did this and I'm
    # not totally sure why...
    os.chdir("/var/tmp")


def run_on_all_hosts(ctx_obj, options, report):
    starttime = time.monotonic()
    host_ids = ctx_obj["host_ids"]
    results = []
    with Progress(console=ctx_obj["console"], refresh_per_second=1) as progress:
        task_global = progress.add_task(f"Crawling {len(host_ids)} mirrors", total=len(host_ids))
        threads_results = run_in_threadpool(
            worker,
            host_ids,
            fn_args=(options, ctx_obj["config"], progress),
            timeout=options["global_timeout"],
            executor_kwargs={
                "max_workers": options["threads"],
            },
        )
        for result in threads_results:
            progress.advance(task_global)
            if result is None:
                # The host has been skipped
                continue
            results.append(result)

    report(ctx_obj, options, results)
    logger.info("Crawler finished after %d seconds", (time.monotonic() - starttime))


@main.command()
@click.option(
    "--canary",
    is_flag=True,
    default=False,
    help="Fast crawl by only checking if mirror can be reached",
)
@click.option(
    "--repodata",
    is_flag=True,
    default=False,
    help="Fast crawl by only checking if the repodata is up to date",
)
@click.pass_context
def crawl(ctx, **kwargs):
    options = ctx.obj["options"]
    options.update(ctx.params)
    run_on_all_hosts(ctx.obj, options, report_crawl)


@main.command()
@click.option(
    "--product",
    help="Product to check (default=all)",
)
@click.option(
    "--version",
    help="Version to check (default=all currently active versions)",
)
@click.pass_context
def propagation(ctx, **kwargs):
    """Records information about repomd.xml propagation and generates graphs.

    Defaults to development/rawhide/x86_64/os/repodata
    """
    options = ctx.obj["options"]
    options.update(ctx.params)
    options["propagation"] = True
    if options["version"] and not options["product"]:
        raise click.BadOptionUsage(
            "--version", "if you select a version, you must select a product."
        )
    if not options["version"]:
        product_versions = get_current_versions(ctx.obj["config"])
        if options["product"]:
            product_versions = [pv for pv in product_versions if pv[0] == options["product"]]
    else:
        product_versions = [(options["product"], options["version"])]
    del options["product"]
    del options["version"]
    options["product_versions"] = product_versions
    logger.info(
        "Propagation will be checked for %s",
        ", ".join(f"{pv[0]} {pv[1]}" for pv in product_versions),
    )
    run_on_all_hosts(ctx.obj, options, record_propagation)


def record_propagation(ctx_obj, options, results: list[PropagationResult]):
    console = ctx_obj["console"]
    config = ctx_obj["config"]
    db_manager = get_db_manager(config)
    repo_status = defaultdict(lambda: defaultdict(lambda: 0))
    for result in results:
        for repo_id, status in result.repo_status.items():
            repo_status[repo_id][status.value] += 1
    now = datetime.now()
    with db_manager.Session() as session:
        for repo_id, status_counts in repo_status.items():
            session.add(model.PropagationStat(repository_id=repo_id, datetime=now, **status_counts))
        report_propagation(console, session, repo_status)
        session.commit()
