import pytest

from mirrormanager2.crawler import continents
from mirrormanager2.crawler.continents import (
    BrokenBaseUrl,
    EmbargoedCountry,
    WrongContinent,
    check_continent,
    filter_continents,
)

# ISO 3166-1 reserves the country codes XA to XZ for user-assigned use, so no
# real country has one of the country codes in these tests.
CONFIG = {"GEOIP_BASE": "/nonexistent", "EMBARGOED_COUNTRIES": ["XC"]}


@pytest.fixture(autouse=True)
def fake_continents(monkeypatch):
    """Replace the real continents, because filter_continents() selects from CONTINENTS."""
    monkeypatch.setattr(continents, "CONTINENTS", ["Atlantis", "Lemuria", "Mu"])


@pytest.fixture()
def resolved_hostnames(monkeypatch):
    """Replace the DNS and GeoIP lookups, and return the list of resolved hostnames."""
    hostnames = []

    def get_host_addresses(hostname):
        hostnames.append(hostname)
        return {"192.0.2.1"}

    monkeypatch.setattr(continents.geo, "get_geoip", lambda base_dir, db_type: None)
    monkeypatch.setattr(continents.geo, "get_host_addresses", get_host_addresses)
    monkeypatch.setattr(continents.geo, "get_country", lambda addresses, geoip_db: "XA")
    monkeypatch.setattr(
        continents, "get_country_continents", lambda session: {"XA": "Atlantis", "XB": "Lemuria"}
    )
    return hostnames


def test_check_continent(resolved_hostnames):
    check_continent(
        CONFIG, {"continents": ["Atlantis"]}, None, "http://mirror.example.com:8080/pub/"
    )
    assert resolved_hostnames == ["mirror.example.com"]


def test_check_continent_wrong_continent(resolved_hostnames):
    with pytest.raises(WrongContinent):
        check_continent(CONFIG, {"continents": ["Lemuria"]}, None, "http://mirror.example.com/pub/")


def test_check_continent_other_continent_excluded(resolved_hostnames):
    check_continent(CONFIG, {"continents": ["^Lemuria"]}, None, "http://mirror.example.com/pub/")


def test_check_continent_embargoed_country(resolved_hostnames):
    config = {**CONFIG, "EMBARGOED_COUNTRIES": ["XA"]}
    with pytest.raises(EmbargoedCountry) as excinfo:
        check_continent(
            config, {"continents": ["Atlantis"]}, None, "http://mirror.example.com/pub/"
        )
    assert excinfo.value.country == "XA"


@pytest.mark.parametrize("url", ["/pub/fedora/", "http://[::1/pub/"])
def test_check_continent_broken_url(resolved_hostnames, url):
    with pytest.raises(BrokenBaseUrl):
        check_continent(CONFIG, {"continents": ["Atlantis"]}, None, url)
    assert resolved_hostnames == []


@pytest.mark.parametrize(
    "asked,expected",
    [
        pytest.param([], ["Atlantis", "Lemuria", "Mu"], id="all"),
        pytest.param(["Mu", "Atlantis"], ["Atlantis", "Mu"], id="include"),
        pytest.param(["^Atlantis"], ["Lemuria", "Mu"], id="exclude"),
        pytest.param(["Atlantis", "Lemuria", "^Lemuria"], ["Atlantis"], id="include-and-exclude"),
    ],
)
def test_filter_continents(asked, expected):
    assert filter_continents(asked) == expected
