# This is very Fedora-specific

import requests

ID_PREFIX_TO_PRODUCT = {
    "FEDORA": "Fedora",
    "FEDORA-EPEL": "EPEL",
}
UPDATES_REPO_PREFIX_FORMAT = {
    "Fedora": "updates-released-f{version}",
    "EPEL": "epel-{version}",
    "CentOS": "centos-baseos-{version}",
}


def get_current_versions(config):
    """Return tuples of the current (Product, Version, RepoPrefix)"""
    # Get all the current releases from Bodhi
    url = f"{config['BODHI_URL']}/releases/"
    page = 1
    pages = 42
    releases = []
    while page <= pages:
        response = requests.get(
            url, {"state": "current", "page": str(page)}, headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        response = response.json()
        pages = response["pages"]
        releases.extend(response["releases"])
        page += 1
    # Deduplicate
    releases = set((r["id_prefix"], r["version"]) for r in releases)
    # Now translate that into MirrorManager Product and Version
    product_versions = [
        (ID_PREFIX_TO_PRODUCT[r[0]], r[1]) for r in releases if r[0] in ID_PREFIX_TO_PRODUCT
    ]
    product_versions.sort(key=lambda pv: f"{pv[0]}--{pv[1]}")
    return product_versions


def get_propagation_repo_prefix(product, version):
    return UPDATES_REPO_PREFIX_FORMAT[product].format(version=version)
