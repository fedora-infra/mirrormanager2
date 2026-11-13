import copy

import pytest

from mirrormanager2.lib.hostconfig import validate_config

VALID_CONFIG = {
    "version": 0,
    "global": {"enabled": "1"},
    "site": {"name": "test-mirror", "password": "test_password"},
    "host": {"name": "mirror.localhost"},
    "stats": {},
    "Fedora Linux": {"dirtree": "/srv/pub/fedora/linux"},
}


def config_with(changes):
    """Return a copy of VALID_CONFIG with the changes applied. A value of None removes the key."""
    config = copy.deepcopy(VALID_CONFIG)
    for key, value in changes.items():
        if value is None:
            del config[key]
        else:
            config[key] = value
    return config


@pytest.mark.parametrize(
    "config,expected",
    [
        pytest.param(config_with({}), (True, ""), id="valid"),
        pytest.param(
            ["not", "a", "dict"],
            (False, "config file is not a dict.\nPlease update your copy of report_mirror.\n"),
            id="not-a-dict",
        ),
        pytest.param(
            config_with({"version": None}),
            (False, "config file has no version field.\n"),
            id="no-version",
        ),
        pytest.param(
            config_with({"host": None}),
            (False, "config file missing section host.\n"),
            id="no-host-section",
        ),
        pytest.param(
            config_with({"global": {"enabled": "0"}}),
            (False, "config file section [global] not enabled.\n"),
            id="global-disabled",
        ),
        pytest.param(
            config_with({"site": {"name": "test-mirror"}}),
            (False, "config file [site] missing required option password.\n"),
            id="site-without-password",
        ),
        pytest.param(
            config_with({"host": {}}),
            (False, "section [host] missing required option name.\n"),
            id="host-without-name",
        ),
        pytest.param(
            config_with({"Fedora Linux": {}}),
            (False, "section [Fedora Linux] missing required option dirtree.\n"),
            id="category-without-dirtree",
        ),
    ],
)
def test_validate_config(config, expected):
    assert validate_config(config) == expected
