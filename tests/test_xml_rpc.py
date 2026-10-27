"""
mirrormanager2 tests for the XML-RPC endpoint.
"""

import base64
import bz2
import json
import xmlrpc.client

import pytest


def xmlrpc_call(client, method, *args):
    """Call method over XML-RPC and return the unmarshalled result."""
    response = client.post(
        "/xmlrpc", data=xmlrpc.client.dumps(args, method), content_type="text/xml"
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/xml")
    result, _method = xmlrpc.client.loads(response.get_data())
    return result[0]


def encode_config(config):
    """Encode config the way report_mirror sends it."""
    return base64.urlsafe_b64encode(bz2.compress(json.dumps(config).encode())).decode()


def test_list_methods(client):
    assert "checkin" in xmlrpc_call(client, "system.listMethods")


def test_checkin_invalid_config(client, db):
    result = xmlrpc_call(client, "checkin", encode_config({"version": 1}))
    assert result == (
        "config file version is not 0, is 1.\n"
        "Invalid config file provided, please check your report_mirror.conf."
        "error checking in"
    )


def test_checkin_not_json(client, db):
    payload = base64.urlsafe_b64encode(bz2.compress(b"not json")).decode()
    assert xmlrpc_call(client, "checkin", payload) == "error checking in"


def test_checkin_unknown_site(client, db):
    config = {
        "version": 0,
        "global": {"enabled": "1"},
        "site": {"name": "no-such-site", "password": "hunter2"},
        "host": {"name": "mirror.localhost"},
    }
    result = xmlrpc_call(client, "checkin", encode_config(config))
    assert result == "Config file site name or password incorrect.\nerror checking in"


def test_unknown_method(client):
    response = client.post("/xmlrpc", data=xmlrpc.client.dumps((), "nope"), content_type="text/xml")
    assert response.status_code == 200
    # An unknown method comes back as an XML-RPC fault, not as an HTTP error.
    with pytest.raises(xmlrpc.client.Fault):
        xmlrpc.client.loads(response.get_data())
