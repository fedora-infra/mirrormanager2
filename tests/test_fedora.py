from responses import matchers

from mirrormanager2.lib.fedora import get_current_versions

BODHI_URL = "https://bodhi.example.com"


def bodhi_release(name, id_prefix, version):
    return {"name": name, "id_prefix": id_prefix, "version": version, "state": "current"}


def test_get_current_versions(mocked_responses):
    mocked_responses.get(
        f"{BODHI_URL}/releases/",
        match=[matchers.query_param_matcher({"state": "current", "page": "1"})],
        json={
            "releases": [
                bodhi_release("F44", "FEDORA", "44"),
                bodhi_release("F43C", "FEDORA-CONTAINER", "43"),
                bodhi_release("EPEL-9N", "FEDORA-EPEL-NEXT", "9"),
                bodhi_release("EPEL-9", "FEDORA-EPEL", "9"),
            ],
            "page": 1,
            "pages": 2,
        },
    )
    mocked_responses.get(
        f"{BODHI_URL}/releases/",
        match=[matchers.query_param_matcher({"state": "current", "page": "2"})],
        json={
            "releases": [
                bodhi_release("F43", "FEDORA", "43"),
                bodhi_release("F44F", "FEDORA-FLATPAK", "44"),
                bodhi_release("EPEL-10.4", "FEDORA-EPEL", "10.4"),
            ],
            "page": 2,
            "pages": 2,
        },
    )

    assert get_current_versions({"BODHI_URL": BODHI_URL}) == [
        ("EPEL", "10.4"),
        ("EPEL", "9"),
        ("Fedora", "43"),
        ("Fedora", "44"),
    ]
