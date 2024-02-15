import logging

import click

from mirrormanager2.lib import get_category_by_name

logger = logging.getLogger(__name__)


config_option = click.option(
    "-c",
    "--config",
    envvar="MM2_CONFIG",
    default="/etc/mirrormanager/mirrormanager2.cfg",
    help="Configuration file to use",
    show_default=True,
)


def filter_master_directories(config, session, category_names):
    include_category_names = [n for n in category_names if not n.startswith("^")]
    exclude_category_names = [n for n in category_names if n.startswith("^")]
    master_directories = []
    for master_dir in config.get("UMDL_MASTER_DIRECTORIES"):
        if include_category_names and master_dir["category"] not in include_category_names:
            continue
        if exclude_category_names and f"^{master_dir['category']}" in exclude_category_names:
            continue
        cname = master_dir["category"]
        category = get_category_by_name(session, cname)
        if not category:
            logger.error(
                "UMDL_MASTER_DIRECTORIES Category %s does not exist in the database, skipping",
                cname,
            )
            continue
        if category.product is None:
            logger.error("UMDL_MASTER_DIRECTORIES Category %s has null Product, skipping", cname)
            continue
        master_dir["category_db"] = category
        master_directories.append(master_dir)
    return master_directories


def setup_logging(debug=False):
    log_format = "[%(asctime)s][%(levelname)s] %(message)s"
    logging.basicConfig(format=log_format, level=logging.DEBUG if debug else logging.INFO)
