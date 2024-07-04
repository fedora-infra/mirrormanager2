"""
mirrormanager2 tests for the Flask application.
"""

import os

import pytest

from mirrormanager2.lib import get_host


@pytest.fixture(autouse=True)
def setup_all(db_items):
    skip = os.getenv("MM2_SKIP_NETWORK_TESTS", 0)
    if skip:
        raise pytest.skip("Skipping FlaskUiAppTest tests")


def test_index(client):
    """Test the index endpoint."""

    output = client.get("/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Home - MirrorManager</title>" in data
    assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data
    assert 'href="/login?next=http://localhost/">Login</a>' in data


def test_index_auth(client, user):
    output = client.get("/")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Home - MirrorManager</title>" in data
    assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data
    assert 'href="/login?next=http://127.0.0.1:5000/">login/a>' not in data
    assert '<a class="dropdown-item" href="/site/mine">My Sites</a>' in data
    assert 'href="/logout?next=http://localhost/">Log Out</a>' in data


def test_list_mirrors(client):
    """Test the list_mirrors endpoint."""
    output = client.get("/mirrors")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Mirrors - MirrorManager</title>" in data
    assert "<h2>Public active mirrors</h2>" in data
    assert "We have currently 2 active mirrors" in data

    for i in [27, 26, 25]:
        output = client.get("/mirrors/Fedora/%s" % i)
        assert output.status_code == 200
        data = output.get_data(as_text=True)
        assert "<title>Mirrors - MirrorManager</title>" in data
        assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data
        assert "We have currently 2 active mirrors" in data

        output = client.get(f"/mirrors/Fedora Linux/{i}/x86_64")
        assert output.status_code == 200
        data = output.get_data(as_text=True)
        assert "<title>Mirrors - MirrorManager</title>" in data
        assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data
        assert "We have currently 2 active mirrors" in data

        output = client.get("/mirrors/Fedora Linux/20/i386")
        assert output.status_code == 200
        data = output.get_data(as_text=True)
        assert "<title>Mirrors - MirrorManager</title>" in data
        assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data
        assert "There are currently no active mirrors registered." in data


def test_mysite(client):
    """Test the mysite endpoint."""
    output = client.get("/site/mine")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/site/mine" in data


def test_mysite_auth(client, user):
    output = client.get("/site/mine")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "1 site" in data


def test_all_sites(client):
    """Test the all_sites endpoint."""
    output = client.get("/admin/all_sites")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/admin/all_sites" in data


def test_all_sites_auth(client, user):
    output = client.get("/admin/all_sites")
    assert output.status_code == 302
    output = client.get("/admin/all_sites", follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">You are not an admin</div>' in data
    assert "<title>Home - MirrorManager</title>" in data
    assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data


def test_all_sites_auth_admin(client, admin_user):
    output = client.get("/admin/all_sites")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>Home - MirrorManager</title>" in data
    assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data
    assert "<h2>Admin - List all Sites</h2>" in data
    assert "3 sites" in data


def test_site_new(client):
    """Test the site_new endpoint."""
    output = client.get("/site/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/site/new" in data


def test_site_new_auth(client, user):
    output = client.get("/site/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>New Site - MirrorManager</title>" in data
    assert "<h4>Export Compliance</h4>" in data
    assert '<label class="form-label" for="name">Site name</label>' in data
    assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {
        "name": "pingoured.fr",
        "password": "foobar",
        "org_url": "http://pingoured.fr",
        "admin_active": True,
        "user_active": True,
    }

    # Check CSRF protection

    output = client.post("/site/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>New Site - MirrorManager</title>" in data
    assert "<h4>Export Compliance</h4>" in data
    assert '<label class="form-label" for="name">Site name</label>' in data
    assert '<a class="nav-link color-white" href="/mirrors">Mirrors</a>' in data

    # Create the new site

    post_data["csrf_token"] = csrf_token

    output = client.post("/site/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Site added</div>' in data
    assert '<div class="toast-body">pingou added as an admin</div>' in data
    assert "<h2>Fedora Public Active Mirrors</h2>" in data

    output = client.get("/site/mine")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "2 sites" in data


def test_site_view(client):
    """Test the site_view endpoint."""
    output = client.get("/site/2")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/site/2" in data


def test_site_view_auth(client, user):
    output = client.get("/site/5")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Site not found</p>" in data

    # Test if accessing other sites is not allowed
    output = client.get("/site/1")
    assert output.status_code == 403

    output = client.get("/site/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert "mirror2.localhost</a>" in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    # Incomplete input
    post_data = {
        "name": "test-mirror2.1",
    }

    output = client.post("/site/2", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert data.count("field is required.") == 2

    post_data = {
        "name": "test-mirror2.1",
        "password": "test_password2",
        "org_url": "http://getfedora.org",
        "admin_active": True,
        "user_active": True,
        "downstream_comments": "Mirror available over HTTP.",
    }

    # Check CSRF protection

    output = client.post("/site/2", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data

    # Update site

    post_data["csrf_token"] = csrf_token

    output = client.post("/site/2", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<h2>Fedora Public Active Mirrors</h2>" in data
    assert '<div class="toast-body">Site Updated</div>' in data

    # Check after the edit
    output = client.get("/site/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "test-mirror2.1</h2>" in data
    assert "kevin" in data
    assert "mirror2.localhost</a>" in data


def test_host_new(client):
    """Test the host_new endpoint."""
    output = client.get("/host/2/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/2/new" in data


def test_host_new_auth(client, user):
    # Invalid site identifier
    output = client.get("/host/5/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Site not found</p>" in data

    # Check before adding the host
    output = client.get("/site/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert "mirror2.localhost</a>" in data
    assert "pingoured.fr</a>" not in data

    # Test host_new
    output = client.get("/host/2/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>New Host - MirrorManager</title>" in data
    assert '<h6 class="mb-0">Add New Host</h6>' in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {
        "name": "pingoured.fr",
        "admin_active": True,
        "user_active": True,
        "country": "FR",
        "bandwidth_int": 100,
        "asn_clients": True,
        "max_connections": 3,
    }

    # Check CSRF protection

    output = client.post("/host/2/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>New Host - MirrorManager</title>" in data
    assert '<h6 class="mb-0">Add New Host</h6>' in data

    # Create Host

    post_data["csrf_token"] = csrf_token

    output = client.post("/host/2/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host added</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert "mirror2.localhost</a>" in data
    assert "pingoured.fr</a>" in data

    # Try creating the same host -- will fail
    output = client.post("/host/2/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Could not create the new host</div>' in data


def test_siteadmin_new(client):
    """Test the siteadmin_new endpoint."""
    output = client.get("/site/2/admin/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/site/2/admin/new" in data


def test_siteadmin_new_auth(client, user):
    # Invalid site identifier
    output = client.get("/site/5/admin/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Site not found</p>" in data

    # Check before adding the host
    output = client.get("/site/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert 'action="/site/2/admin/5/delete">' not in data
    assert "skvidal" not in data

    # Test host_new
    output = client.get("/site/2/admin/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>New Site Admin - MirrorManager</title>" in data
    assert '<h6 class="mb-0">Add Site admin to site: test-mirror2</h6>' in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {
        "username": "skvidal",
    }

    # Check CSRF protection

    output = client.post("/site/2/admin/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<title>New Site Admin - MirrorManager</title>" in data
    assert '<h6 class="mb-0">Add Site admin to site: test-mirror2</h6>' in data

    # Create Admin

    post_data["csrf_token"] = csrf_token

    output = client.post("/site/2/admin/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Site Admin added</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert 'action="/site/2/admin/3/delete">' in data
    assert "skvidal" in data


def test_siteadmin_delete(client):
    """Test the siteadmin_delete endpoint."""
    output = client.post("/site/2/admin/3/delete")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/site/2/admin/3/delete" in data


def test_siteadmin_delete_auth(client, user):
    # Check before adding the host
    output = client.get("/site/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert 'action="/site/2/admin/3/delete">' in data
    assert data.count("</span> ralph") == 1

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {}

    # Check CSRF protection

    output = client.post("/site/2/admin/3/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert 'action="/site/2/admin/3/delete">' in data
    assert data.count("</span> ralph") == 1

    # Delete Site Admin

    post_data["csrf_token"] = csrf_token

    # Invalid site identifier
    output = client.post("/site/5/admin/3/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Site not found</p>" in data

    # Invalid site admin identifier
    output = client.post("/site/2/admin/9/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Site Admin not found</p>" in data

    # Valid site admin but not for this site
    output = client.post("/site/2/admin/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Site Admin not related to this Site</p>" in data

    # Delete Site Admin
    output = client.post("/site/2/admin/3/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-globe"></span> test-mirror2</h2>' in data
    assert "kevin" in data
    assert 'action="/site/2/admin/3/delete">' not in data
    assert data.count("</span> ralph") == 0

    # Trying to delete the only admin
    output = client.post("/site/2/admin/4/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert (
        '<div class="toast-body">There is only one admin set, you cannot ' "delete it.</div>"
    ) in data


def test_host_view(client):
    """Test the host_view endpoint."""
    output = client.get("/host/5")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/5" in data


def test_host_view_auth(client, user):
    output = client.get("/host/50")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    # Test if accessing other hosts is not allowed
    output = client.get("/host/3")
    assert output.status_code == 403

    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    # Incomplete input
    post_data = {
        "name": "private.localhost.1",
    }

    output = client.post("/host/2", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data
    assert data.count("field is required.") == 3

    post_data = {
        "name": "private.localhost.1",
        "admin_active": True,
        "user_active": True,
        "country": "NL",
        "bandwidth_int": 100,
        "asn_clients": True,
        "max_connections": 10,
        "comment": "My own private mirror",
    }

    # Check CSRF protection

    output = client.post("/host/2", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data

    # Update site

    post_data["csrf_token"] = csrf_token

    output = client.post("/host/2", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost.1' in data


def test_host_netblock_new(client):
    """Test the host_netblock_new endpoint."""
    output = client.get("/host/3/netblock/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/3/netblock/new" in data


def test_host_netblock_new_auth(client, another_user):
    output = client.get("/host/50/netblock/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    output = client.get("/host/3/netblock/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host netblock</h6>' in data
    assert "<title>New Host netblock - MirrorManager</title>" in data
    assert 'action="/host/3/host_netblock/2/delete">' not in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {
        "netblock": "192.168.0.0/24",
        "name": "home network",
    }

    # Check CSRF protection

    output = client.post("/host/3/netblock/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host netblock</h6>' in data
    assert "<title>New Host netblock - MirrorManager</title>" in data
    assert 'action="/host/3/host_netblock/1/delete">' not in data

    # Update site

    post_data["csrf_token"] = csrf_token

    output = client.post("/host/3/netblock/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host netblock added</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_netblock/2/delete">' in data


def test_host_netblock_delete(client):
    """Test the host_netblock_delete endpoint."""
    output = client.post("/host/3/host_netblock/1/delete")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/3/host_netblock/1/delete" in data


def test_host_netblock_delete_auth(client, another_user):
    # Check before adding the host
    output = client.get("/host/3")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_netblock/1/delete">' in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {}

    # Check CSRF protection

    output = client.post("/host/3/host_netblock/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_netblock/1/delete">' in data

    # Delete Site Admin

    post_data["csrf_token"] = csrf_token

    # Invalid site identifier
    output = client.post("/host/5/host_netblock/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    # Invalid site admin identifier
    output = client.post("/host/3/host_netblock/2/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host netblock not found</p>" in data

    # Delete Site Admin
    output = client.post("/host/3/host_netblock/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host netblock deleted</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_netblock/1/delete">' not in data


def test_host_asn_new(client):
    """Test the host_asn_new endpoint."""
    output = client.get("/host/3/asn/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/3/asn/new" in data


def test_host_asn_new_auth(client, admin_user):
    output = client.get("/host/50/asn/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    output = client.get("/host/3/asn/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host Peer ASNs</h6>' in data
    assert "<title>New Host Peer ASN - MirrorManager</title>" in data
    assert 'action="/host/3/host_asn/2/delete">' not in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {
        "asn": "192168",
        "name": "ASN pingoured",
    }

    # Check CSRF protection

    output = client.post("/host/3/asn/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host Peer ASNs</h6>' in data
    assert "<title>New Host Peer ASN - MirrorManager</title>" in data
    assert 'action="/host/3/host_asn/2/delete">' not in data

    # Update site

    post_data["csrf_token"] = csrf_token

    output = client.post("/host/3/asn/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host Peer ASN added</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_asn/2/delete">' in data


def test_host_asn_delete(client):
    """Test the host_asn_delete endpoint."""
    output = client.post("/host/3/host_asn/1/delete")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/3/host_asn/1/delete" in data


def test_host_asn_delete_auth(client, admin_user):
    # Check before adding the host
    output = client.get("/host/3")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_asn/1/delete">' in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {}

    # Check CSRF protection

    output = client.post("/host/3/host_asn/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_asn/1/delete">' in data

    # Delete Host ASN

    post_data["csrf_token"] = csrf_token

    # Invalid site identifier
    output = client.post("/host/5/host_asn/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    # Invalid Host ASN identifier
    output = client.post("/host/3/host_asn/2/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host Peer ASN not found</p>" in data

    # Delete Host ASN
    output = client.post("/host/3/host_asn/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host Peer ASN deleted</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_asn/1/delete">' not in data


def test_host_country_new(client):
    """Test the host_country_new endpoint."""
    output = client.get("/host/5/country/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/5/country/new" in data


def test_host_country_new_auth(client, another_user):
    output = client.get("/host/50/country/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    output = client.get("/host/3/country/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host country allowed</h6>' in data
    assert "<title>New Host Country - MirrorManager</title>" in data
    assert 'action="/host/3/host_country/3/delete">' not in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {
        "country": "GB",
    }

    # Check CSRF protection

    output = client.post("/host/3/country/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host country allowed</h6>' in data
    assert "<title>New Host Country - MirrorManager</title>" in data
    assert 'action="/host/3/host_country/3/delete">' not in data

    # Invalid Country code

    post_data["csrf_token"] = csrf_token

    output = client.post("/host/3/country/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Invalid country code</div>' in data
    assert '<h6 class="mb-0">Add host country allowed</h6>' in data
    assert "<title>New Host Country - MirrorManager</title>" in data
    assert 'action="/host/3/host_country/3/delete">' not in data

    # Create Country

    post_data["country"] = "FR"

    output = client.post("/host/3/country/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host Country added</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> private.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/3/host_country/3/delete">' in data


def test_host_country_delete(client):
    """Test the host_country_delete endpoint."""
    output = client.post("/host/1/host_country/1/delete")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/1/host_country/1/delete" in data


def test_host_country_delete_auth(client, another_user):
    # Check before adding the host
    output = client.get("/host/1")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/1/host_country/1/delete">' in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {}

    # Check CSRF protection

    output = client.post("/host/1/host_country/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/1/host_country/1/delete">' in data

    # Delete Host Country

    post_data["csrf_token"] = csrf_token

    # Invalid site identifier
    output = client.post("/host/5/host_country/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    # Invalid Host Country identifier
    output = client.post("/host/1/host_country/5/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host Country not found</p>" in data

    # Delete Host Country
    output = client.post("/host/1/host_country/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host Country deleted</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/1/host_country/1/delete">' not in data


def test_host_category_new(client):
    """Test the host_category_new endpoint."""
    output = client.get("/host/5/category/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/5/category/new" in data


def test_host_category_new_auth(client, user):
    output = client.get("/host/50/category/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    output = client.get("/host/2/category/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host category</h6>' in data
    assert "<title>New Host Category - MirrorManager</title>" in data
    assert 'action="/host/2/category/1/delete">' not in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {
        "category_id": "Fedora Linux",
    }

    # Invalid input

    output = client.post("/host/2/category/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host category</h6>' in data
    assert "<title>New Host Category - MirrorManager</title>" in data
    assert 'action="/host/2/category/1/delete">' not in data
    assert "Invalid Choice: could not coerce" in data

    # Check CSRF protection

    output = client.post("/host/2/category/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host category</h6>' in data
    assert "<title>New Host Category - MirrorManager</title>" in data
    assert 'action="/host/2/category/1/delete">' not in data

    # Delete before adding

    post_data["csrf_token"] = csrf_token

    output = client.post("/host/2/category/4/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200

    # Add Category

    post_data["csrf_token"] = csrf_token
    post_data["category_id"] = "2"

    output = client.post("/host/2/category/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host Category added</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data

    # Try adding the same Category -- fails

    output = client.post("/host/2/category/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Could not add Category to the host</div>' in data
    assert '<h6 class="mb-0">Add host category</h6>' in data
    assert "<title>New Host Category - MirrorManager</title>" in data
    assert 'action="/host/2/category/1/delete">' not in data

    # Check host after adding the category
    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/2/category/4/delete">' in data


def test_host_category_new_as_admin(client):
    """Test the host_category_new endpoint."""
    output = client.get("/host/5/category/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/5/category/new" in data


def test_host_category_new_as_admin_auth(client, admin_user):
    output = client.get("/host/50/category/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    output = client.get("/host/2/category/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host category</h6>' in data
    assert "<title>New Host Category - MirrorManager</title>" in data
    assert 'action="/host/2/category/1/delete">' not in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {}
    post_data["csrf_token"] = csrf_token
    output = client.post("/host/2/category/4/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200

    # Add Category

    post_data["csrf_token"] = csrf_token
    # 3 is an admin only category
    post_data["category_id"] = "3"

    output = client.post("/host/2/category/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host Category added</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data

    # Try adding the same Category -- fails

    output = client.post("/host/2/category/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Could not add Category to the host</div>' in data
    assert '<h6 class="mb-0">Add host category</h6>' in data
    assert "<title>New Host Category - MirrorManager</title>" in data
    assert 'action="/host/2/category/1/delete">' not in data


def test_host_category_delete(client):
    """Test the host_category_delete endpoint."""
    output = client.post("/host/1/category/1/delete")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/1/category/1/delete" in data


def test_host_category_delete_auth(client, user):
    # Check before deleting the category
    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/2/category/3/delete">' in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {}

    # Check CSRF protection

    output = client.post("/host/2/category/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/2/category/3/delete">' in data

    # Delete Host Category

    post_data["csrf_token"] = csrf_token

    # Invalid site identifier
    output = client.post("/host/5/category/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    # Invalid Host Category identifier
    output = client.post("/host/2/category/50/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host/Category not found</p>" in data

    # Invalid Host/Category association
    output = client.post("/host/2/category/1/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Category not associated with this host</p>" in data

    # Delete Host Category
    output = client.post("/host/2/category/3/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host Category deleted</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span> mirror2.localhost' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/2/category/1/delete">' not in data


def test_host_category_url_new(client):
    """Test the host_category_url_new endpoint."""
    output = client.get("/host/1/category/1/url/new")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/1/category/1/url/new" in data


def test_host_category_url_new_auth(client, user):
    output = client.get("/host/50/category/1/url/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    output = client.get("/host/2/category/50/url/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host/Category not found</p>" in data

    output = client.get("/host/2/category/1/url/new")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Category not associated with this host</p>" in data

    output = client.get("/host/2/category/3/url/new")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host category URL</h6>' in data
    assert "<title>New Host Category URL - MirrorManager</title>" in data
    assert 'action="/host/2/category/3/url/5/delete">' not in data

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {
        "url": "http://pingoured.fr/pub/Fedora/",
    }

    # Check CSRF protection

    output = client.post("/host/2/category/3/url/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h6 class="mb-0">Add host category URL</h6>' in data
    assert "<title>New Host Category URL - MirrorManager</title>" in data
    assert 'action="/host/2/category/3/url/5/delete">' not in data

    # Add Host Category URL

    post_data["csrf_token"] = csrf_token

    output = client.post("/host/2/category/3/url/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host Category URL added</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span>' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/2/category/3/url/9/delete">' in data

    # Try adding the same Host Category URL -- fails

    post_data["csrf_token"] = csrf_token

    output = client.post("/host/2/category/3/url/new", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "Could not add Category URL to the host" in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span>' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/2/category/3/url/9/delete">' in data


def test_host_category_url_delete(client):
    """Test the host_category_url_delete endpoint."""
    output = client.post("/host/1/category/1/url/3/delete")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/1/category/1/url/3/delete" in data


def test_host_category_url_delete_auth(client, user):
    # Check before deleting the category URL
    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)

    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    post_data = {}

    # Check CSRF protection

    output = client.post("/host/2/category/3/url/5/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<h2 class="mb-0"><span class="fa fa-server"></span>' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/2/category/3/url/5/delete">' in data

    # Delete Host Category URL

    post_data["csrf_token"] = csrf_token

    # Invalid site identifier
    output = client.post("/host/5/category/5/url/5/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    # Invalid Host Category identifier
    output = client.post("/host/2/category/50/url/5/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host/Category not found</p>" in data

    # Invalid Host/Category association
    output = client.post("/host/2/category/3/url/4/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Category URL not associated with this host</p>" in data

    # Invalid Category/URL
    output = client.post("/host/2/category/3/url/50/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host category URL not found</p>" in data

    # Invalid Category/URL association
    output = client.post("/host/2/category/2/url/4/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Category not associated with this host</p>" in data

    # Delete Host Category URL
    output = client.post("/host/2/category/3/url/5/delete", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">Host category URL deleted</div>' in data
    assert '<h2 class="mb-0"><span class="fa fa-server"></span>' in data
    assert "<title>Host - MirrorManager</title>" in data
    assert 'action="/host/2/category/3/url/5/delete">' not in data


def test_auth_logout(client):
    """Test the auth_logout endpoint."""
    output = client.get("/logout")
    assert output.status_code == 302

    output = client.get("/logout", follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<h2>Fedora Public Active Mirrors</h2>" in data


def test_auth_logout_auth(client, user):
    output = client.get("/logout")
    assert output.status_code == 302

    output = client.get("/logout", follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert '<div class="toast-body">You were successfully logged out.</div>' in data
    assert "<h2>Fedora Public Active Mirrors</h2>" in data


def test_toggle_private_flag_host(client):
    """
    Test that the toggling of the private flag in the host
    deletes all host category directories.
    """
    output = client.get("/host/2")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/2" in data


def test_toggle_private_flag_host_auth(client, user):
    output = client.get("/host/50")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "pub/fedora/linux/releases/27" in data

    output = client.get("/host/2")
    data = output.get_data(as_text=True)
    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    # Toggle private flag -> private: True
    post_data = {
        "name": "mirror2.localhost",
        "admin_active": True,
        "private": True,
        "user_active": True,
        "country": "FR",
        "bandwidth_int": 100,
        "asn_clients": True,
        "max_connections": 10,
        "csrf_token": csrf_token,
    }

    output = client.post("/host/2", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)

    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    # Make sure the host_category_directory is gone
    assert "pub/fedora/linux/releases/27" not in data


def test_toggle_private_flag_host_auth_more(client, user, db, hostcategorydir_one_more):
    # Get the CSRF
    output = client.get("/host/2")
    data = output.get_data(as_text=True)
    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]
    # Mark the host as private
    hostobj = get_host(db, 2)
    hostobj.private = True
    db.commit()
    # Check the setup is good
    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "pub/fedora/linux/updates/testing/26/x86_64" in data

    # Toggle private flag -> private: False (or rather None)
    post_data = {
        "name": "mirror2.localhost",
        "admin_active": True,
        "private": None,
        "user_active": True,
        "country": "FR",
        "bandwidth_int": 100,
        "asn_clients": True,
        "max_connections": 10,
        "csrf_token": csrf_token,
    }

    # output = client.post('/host/2', data=post_data, follow_redirects=True)
    output = client.post("/host/2", data=post_data)
    assert output.status_code == 302
    # data = output.get_data(as_text=True)
    # print(data)

    output = client.get("/host/2")
    # output = client.get('/host/2')
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    print(data)
    # Make sure the host_category_directory is gone
    assert "pub/fedora/linux/updates/testing/26/x86_64" not in data


def test_toggle_private_flag_site(client):
    """
    Test that the toggling of the private flag in the site
    deletes all host category directories.
    """
    output = client.get("/host/2")
    assert output.status_code == 302
    data = output.get_data(as_text=True)
    assert "/login?next=http://localhost/host/2" in data


def test_toggle_private_flag_site_auth(client, user):
    output = client.get("/host/50")
    assert output.status_code == 404
    data = output.get_data(as_text=True)
    assert "<p>Host not found</p>" in data

    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "pub/fedora/linux/releases/27" in data


def test_toggle_private_flag_site_auth_more(client, user, hostcategorydir_even_more):
    # more test data
    output = client.get("/host/2")
    data = output.get_data(as_text=True)
    csrf_token = data.split('name="csrf_token" type="hidden" value="')[1].split('">')[0]

    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "pub/fedora/linux/updates/testing/27/x86_64" in data

    post_data = {
        "name": "test-mirror2.1",
        "password": "test_password2",
        "org_url": "http://getfedora.org",
        "admin_active": True,
        "user_active": True,
        "private": True,
        "downstream_comments": "Mirror available over HTTP.",
        "csrf_token": csrf_token,
    }

    output = client.post("/site/2", data=post_data, follow_redirects=True)
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    assert "<h2>Fedora Public Active Mirrors</h2>" in data
    assert '<div class="toast-body">Site Updated</div>' in data

    output = client.get("/host/2")
    assert output.status_code == 200
    data = output.get_data(as_text=True)
    # Make sure the host_category_directory is gone
    assert "pub/fedora/linux/updates/testing/27/x86_64" not in data
