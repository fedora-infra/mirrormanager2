import logging

from mirrormanager2 import default_config
from mirrormanager2.lib import get_category_by_name

logger = logging.getLogger(__name__)


def read_config(filename):
    config = dict()
    for key in dir(default_config):
        if key.isupper():
            config[key] = getattr(default_config, key)
    with open(filename) as fh:
        exec(compile(fh.read(), filename, "exec"), config)
    return config


def get_filtered_categories(config, session, only_category):
    categories = []
    for master_dir in config.get("UMDL_MASTER_DIRECTORIES"):
        if only_category is not None and master_dir["category"] != only_category:
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
        categories.append(master_dir)
    return categories


def setup_logging(debug=False):
    log_format = "[%(asctime)s][%(levelname)s] %(message)s"
    logging.basicConfig(format=log_format, level=logging.DEBUG if debug else logging.INFO)
