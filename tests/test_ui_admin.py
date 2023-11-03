"""
mirrormanager2 tests for the Flask UI Admin controller.
"""

import re
from unittest.mock import Mock, patch

import pytest

# TODO: use parametrize


@pytest.fixture(autouse=True)
def setup_all(db_items, mock_oidc):
    pass


def handle_flask_admin_urls(client, url):
    if url.endswith("/"):
        url = url[:-1]
    output = client.get(url + "view/")
    if output.status_code == 404:
        output = client.get(url + "/")
    assert output.status_code == 200
    return output


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin(client, user):
    """Test the admin function."""
    output = client.get("/admin/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Home - Admin</title>" in data
    assert '<a href="/admin/archview/">Arch</a>' not in data
    assert '<a href="/admin/categoryview/">Category</a>' not in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_auth(client, admin_user):
    output = client.get("/admin/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Home - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_arch(client, admin_user):
    """Test the admin Arch view."""
    output = handle_flask_admin_urls(client, "/admin/arch/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Arch - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/arch(view)?/\?sort=0" ' 'title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (4)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_category(client, admin_user):
    """Test the admin Category view."""
    output = handle_flask_admin_urls(client, "/admin/category/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Category - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/category(view)?/\?sort=[02]" ' 'title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (3)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_country(client, admin_user):
    """Test the admin Country view."""
    output = handle_flask_admin_urls(client, "/admin/country/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Country - Country - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/country(view)?/\?sort=0" title="Sort by Code">Code</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (2)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_countrycontinentredirectview(client, admin_user):
    """Test the admin CountryContinentRedirect view."""
    output = handle_flask_admin_urls(client, "/admin/countrycontinentredirect/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Country - Country Continent Redirect - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/countrycontinentredirect(view)?/\?sort=0" '
            'title="Sort by Country">Country</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (3)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_embargoedcountryview(client, admin_user):
    """Test the admin EmbargoedCountry view."""
    output = handle_flask_admin_urls(client, "/admin/embargoedcountry/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Country - Embargoed Country - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/embargoedcountry(view)?/\?sort=0" '
            'title="Sort by Country Code">Country Code</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_directoryview(client, admin_user):
    """Test the admin Directory view."""
    output = handle_flask_admin_urls(client, "/admin/directory/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Directory - Directory - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/directory(view)?/\?sort=0" title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (9)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_directoryexclusivehostview(client, admin_user):
    """Test the admin DirectoryExclusiveHost view."""
    output = handle_flask_admin_urls(client, "/admin/directoryexclusivehost/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Directory - Directory Exclusive Host - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert data.count('<th class="column-header ') == 3
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_filedetailview(client, admin_user):
    """Test the admin FileDetail view."""
    output = handle_flask_admin_urls(client, "/admin/filedetail/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>File - File Detail - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/filedetail(view)?/\?sort=[01]" title="Sort by Filename">Filename</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_filedetailfilegroupview(client, admin_user):
    """Test the admin FileDetailFileGroup view."""
    output = handle_flask_admin_urls(client, "/admin/filedetailfilegroup/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>File - File Detail File Group - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert data.count('<th class="column-header ') == 0
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_filegroupview(client, admin_user):
    """Test the admin FileGroup view."""
    output = handle_flask_admin_urls(client, "/admin/filegroup/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>File - File Group - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/filegroup(view)?/\?sort=0" title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostview(client, admin_user):
    """Test the admin Host view."""
    output = handle_flask_admin_urls(client, "/admin/host/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/host(view)?/\?sort=[0-9]" title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (4)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostaclipview(client, admin_user):
    """Test the admin Host Acl Ip view."""
    output = handle_flask_admin_urls(client, "/admin/hostaclip/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Acl Ip - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/hostaclip(view)?/\?sort=[01]" ' 'title="Sort by Ip">Ip</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostcategoryview(client, admin_user):
    """Test the admin Host Category view."""
    output = handle_flask_admin_urls(client, "/admin/hostcategory/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Category - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/hostcategory(view)?/\?sort=[02]" '
            'title="Sort by Always Up2Date">Always Up2Date</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (4)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostcategorydirview(client, admin_user):
    """Test the admin Host Category Dir view."""
    output = handle_flask_admin_urls(client, "/admin/hostcategorydir/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Category Dir - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/hostcategorydir(view)?/\?sort=[02]" title="Sort by Path">Path</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (2)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostcategoryurlview(client, admin_user):
    """Test the admin Host Category Url view."""
    output = handle_flask_admin_urls(client, "/admin/hostcategoryurl/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Category Url - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/hostcategoryurl(view)?/\?sort=[01]" title="Sort by Url">Url</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (8)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostcountryview(client, admin_user):
    """Test the admin Host Country view."""
    output = handle_flask_admin_urls(client, "/admin/hostcountry/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Country - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert data.count('<th class="column-header ') == 2
    assert '<a href="javascript:void(0)">List (2)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostcountryallowedview(client, admin_user):
    """Test the admin Host Country Allowed view."""
    output = handle_flask_admin_urls(client, "/admin/hostcountryallowed/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Country Allowed - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/hostcountryallowed(view)?/\?sort=[01]" '
            'title="Sort by Country">Country</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostlocationview(client, admin_user):
    """Test the admin Host Location view."""
    output = handle_flask_admin_urls(client, "/admin/hostlocation/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Location - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert data.count('<th class="column-header ') == 2
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostnetblockview(client, admin_user):
    """Test the admin Host Netblock view."""
    output = handle_flask_admin_urls(client, "/admin/hostnetblock/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Netblock - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/hostnetblock(view)?/\?sort=[012]" title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (1)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hostpeerasnview(client, admin_user):
    """Test the admin Host Peer Asn view."""
    output = handle_flask_admin_urls(client, "/admin/hostpeerasn/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Peer Asn - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/hostpeerasn(view)?/\?sort=[012]" title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (1)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_hoststatsview(client, admin_user):
    """Test the admin Host Stats view."""
    output = handle_flask_admin_urls(client, "/admin/hoststats/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Host - Host Stats - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/hoststats(view)?/\?sort=[02]" title="Sort by Type">Type</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_locationview(client, admin_user):
    """Test the admin Location view."""
    output = handle_flask_admin_urls(client, "/admin/location/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Location - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/location(view)?/\?sort=0" title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (3)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_netblockcountryview(client, admin_user):
    """Test the admin Netblock Country view."""
    output = handle_flask_admin_urls(client, "/admin/netblockcountry/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Netblock Country - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/netblockcountry(view)?/\?sort=0" '
            r'title="Sort by Netblock">Netblock</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (1)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_productview(client, admin_user):
    """Test the admin Product view."""
    output = handle_flask_admin_urls(client, "/admin/product/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Product - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/product(view)?/\?sort=0" title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (2)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_repositoryview(client, admin_user):
    """Test the admin Repository view."""
    output = handle_flask_admin_urls(client, "/admin/repository/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Repository - Repository - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/repository(view)?/\?sort=[0-4]" title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (4)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_repositoryredirectview(client, admin_user):
    """Test the admin Repository Redirect view."""
    output = handle_flask_admin_urls(client, "/admin/repositoryredirect/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Repository - Repository Redirect - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/repositoryredirect(view)?/\?sort=0" '
            r'title="Sort by To Repo">To Repo</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (3)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_siteview(client, admin_user):
    """Test the admin Site view."""
    output = handle_flask_admin_urls(client, "/admin/site/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Site - Site - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(r'<a href="/admin/site(view)?/\?sort=0" title="Sort by Name">Name</a>', data)
        is not None
    )
    assert '<a href="javascript:void(0)">List (3)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_siteadminview(client, admin_user):
    """Test the admin Site Admin view."""
    output = handle_flask_admin_urls(client, "/admin/siteadmin/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Site - Site Admin - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/siteadmin(view)?/\?sort=[01]" title="Sort by Username">Username</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (5)</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_sitetositeview(client, admin_user):
    """Test the admin Site To Site view."""
    output = handle_flask_admin_urls(client, "/admin/sitetosite/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Site - Site To Site - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/sitetosite(view)?/\?sort=[0-2]" '
            'title="Sort by Username">Username</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List</a>' in data


@patch("mirrormanager2.app.is_mirrormanager_admin", Mock(return_value=None))
def test_admin_versionview(client, admin_user):
    """Test the admin Version view."""
    output = handle_flask_admin_urls(client, "/admin/version/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Version - Admin</title>" in data
    assert re.search('<a href="/admin/arch(view)?/">Arch</a>', data) is not None
    assert re.search('<a href="/admin/category(view)?/">Category</a>', data) is not None
    assert (
        re.search(
            r'<a href="/admin/version(view)?/\?sort=[01]" ' 'title="Sort by Name">Name</a>',
            data,
        )
        is not None
    )
    assert '<a href="javascript:void(0)">List (6)</a>' in data
