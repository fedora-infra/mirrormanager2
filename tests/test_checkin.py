"""
mirrormanager2 tests for the API `/api/checkin` endpoint.
"""

import base64
import bz2
import json

import pytest


@pytest.fixture(autouse=True)
def setup_all(db_items):
    """Setup database items for all tests."""
    pass


def test_checkin_no_json_missing_data(client):
    """Test /api/checkin with missing data parameter."""
    output = client.post(
        "/api/checkin",
        json={},
    )
    assert output.status_code == 400
    data = output.get_json()
    assert "message" in data
    assert "Missing data parameter" in data["message"]


def test_checkin_invalid_json(client):
    """Test /api/checkin with invalid JSON in compressed data."""
    compressed = bz2.compress(b"not valid json")
    encoded = base64.urlsafe_b64encode(compressed).decode()
    output = client.post(
        "/api/checkin",
        json={"data": encoded},
    )
    assert output.status_code == 400
    data = output.get_json()
    assert "message" in data
    assert "Invalid data" in data["message"]


def test_checkin_missing_global_section(client):
    """Test /api/checkin with missing global section."""
    config = {
        "version": 0,
        "site": {"name": "test-mirror", "password": "test_password"},
        "host": {"name": "mirror.localhost"},
    }
    compressed = bz2.compress(json.dumps(config).encode())
    encoded = base64.urlsafe_b64encode(compressed).decode()
    output = client.post(
        "/api/checkin",
        json={"data": encoded},
    )
    assert output.status_code == 400
    data = output.get_json()
    assert "message" in data
    assert "error checking in" in data["message"]


def test_checkin_success(client):
    """Test /api/checkin with valid private host."""
    config = {
        "version": 0,
        "global": {"enabled": "1"},
        "site": {"name": "test-mirror", "password": "test_password"},
        "host": {"name": "private.localhost"},
        "Fedora Linux": {
            "dirtree": {
                "": {},
            }
        },
    }
    compressed = bz2.compress(json.dumps(config).encode())
    encoded = base64.urlsafe_b64encode(compressed).decode()
    output = client.post(
        "/api/checkin",
        json={"data": encoded},
    )
    assert output.status_code == 200
    data = output.get_json()
    assert "message" in data
    assert "checked in successfully" in data["message"]
    assert "\n" not in data["message"]
    assert not data["message"].startswith(" ")


def test_checkin_wrong_site_name(client):
    """Test /api/checkin with wrong site name."""
    config = {
        "version": 0,
        "global": {"enabled": "1"},
        "site": {"name": "nonexistent-site", "password": "test_password"},
        "host": {"name": "private.localhost"},
        "Fedora Linux": {
            "dirtree": {
                "": {},
            }
        },
    }
    compressed = bz2.compress(json.dumps(config).encode())
    encoded = base64.urlsafe_b64encode(compressed).decode()
    output = client.post(
        "/api/checkin",
        json={"data": encoded},
    )
    assert output.status_code == 400
    data = output.get_json()
    assert "message" in data
    assert "error checking in" in data["message"]


def test_checkin_wrong_password(client):
    """Test /api/checkin with wrong password."""
    config = {
        "version": 0,
        "global": {"enabled": "1"},
        "site": {"name": "test-mirror", "password": "wrong_password"},
        "host": {"name": "private.localhost"},
        "Fedora Linux": {
            "dirtree": {
                "": {},
            }
        },
    }
    compressed = bz2.compress(json.dumps(config).encode())
    encoded = base64.urlsafe_b64encode(compressed).decode()
    output = client.post(
        "/api/checkin",
        json={"data": encoded},
    )
    assert output.status_code == 400
    data = output.get_json()
    assert "message" in data
    assert "error checking in" in data["message"]


def test_checkin_public_host(client):
    """Test /api/checkin with public host (private=False).

    Hosts with private=False should be rejected by read_host_config
    since this endpoint is only for private hosts.
    """
    config = {
        "version": 0,
        "global": {"enabled": "1"},
        "site": {"name": "test-mirror", "password": "test_password"},
        "host": {"name": "mirror.localhost"},
        "Fedora Linux": {
            "dirtree": {
                "": {},
            }
        },
    }
    compressed = bz2.compress(json.dumps(config).encode())
    encoded = base64.urlsafe_b64encode(compressed).decode()
    output = client.post(
        "/api/checkin",
        json={"data": encoded},
    )
    assert output.status_code == 400
    data = output.get_json()
    assert "message" in data
    assert "error checking in" in data["message"]


def test_checkin_invalid_base64(client):
    """Test /api/checkin with invalid base64 data."""
    output = client.post(
        "/api/checkin",
        json={"data": "not-valid-base64!@#$%"},
    )
    assert output.status_code == 400
    data = output.get_json()
    assert "message" in data
    assert "Invalid data" in data["message"]


def test_checkin_invalid_bz2(client):
    """Test /api/checkin with invalid bz2 compressed data."""
    invalid_data = base64.urlsafe_b64encode(b"not bz2 compressed data").decode()
    output = client.post(
        "/api/checkin",
        json={"data": invalid_data},
    )
    assert output.status_code == 400
    data = output.get_json()
    assert "message" in data
    assert "Invalid data" in data["message"]
