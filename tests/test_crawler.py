# Copyright © 2017  Adrian Reber
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""
mirrormanager2 tests for the crawler.
"""

import os
from datetime import datetime
from unittest.mock import Mock

import pytest
import requests
import sqlalchemy as sa
from fedora_messaging.testing import mock_sends
from mirrormanager_messages.host import HostCrawlerDisabledV1

from mirrormanager2 import default_config
from mirrormanager2.crawler.connection_pool import ConnectionPool
from mirrormanager2.crawler.connector import FetchingFailed
from mirrormanager2.crawler.crawler import CrawlResult
from mirrormanager2.crawler.reporter import store_crawl_result
from mirrormanager2.crawler.states import CrawlStatus
from mirrormanager2.lib import model
from mirrormanager2.lib.sync import run_rsync

FOLDER = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def config():
    config = dict()
    for key in dir(default_config):
        if key.isupper():
            config[key] = getattr(default_config, key)
    config.update(
        {
            "TESTING": True,
            "SERVER_NAME": "mirrormanager.example.com",
            "OIDC_CLIENT_SECRETS": os.path.join(FOLDER, "client_secrets.json"),
        }
    )
    return config


@pytest.fixture()
def dir_obj(db):
    """Test scanning empty directories."""
    directory = model.Directory(
        name="pub/fedora/linux/releases/20",
        readable=True,
    )
    db.add(directory)
    db.commit()
    return directory


@pytest.fixture()
def dir_obj_with_files(db, dir_obj):
    dir_obj.files = {"does-not-exist": {"size": 1, "stat": 1}}
    db.commit()
    return dir_obj


def test_run_rsync():
    """Test the run_rsync function"""

    # Test timeout if timeout works

    # Travis needs a really small timeout value
    result, fd = run_rsync("/", timeout=0.05)
    fd.close()
    assert result == -9

    # Test if timeout does not trigger
    result, fd = run_rsync(".", timeout=10)
    fd.close()
    assert result != -9

    # Test with non-existing directory
    result, fd = run_rsync("this-is-not-here-i-hope--")
    fd.close()
    assert result == 23
    assert result != 0

    # Test the 'normal' usage
    dest = FOLDER + "/../testdata/"
    result, fd = run_rsync(dest)
    assert result == 0
    output = ""
    while True:
        line = fd.readline()
        if not line:
            break
        output += line

    fd.close()

    for i in [
        "20/Live/x86_64/Fedora-Live-x86_64-20-CHECKSUM",
        "pub/fedora/linux/releases/20/Fedora/",
        "releases/20/Fedora/source/SRPMS/a/aalib-1.4.0-0.23",
        "pub/fedora/linux/development/22/x86_64/os/repodata",
    ]:
        assert i in output

    # Test the 'extra_rsync_args'
    extra = "--exclude *aalib*"
    result, fd = run_rsync(dest, extra)
    assert result == 0
    output = ""
    while True:
        line = fd.readline()
        if not line:
            break
        output += line

    fd.close()

    # Check that aalib is excluded
    assert "aalib" not in output

    # Check that non-excluded files are still included
    assert "fedora/linux/development/22/" in output


def test_scan_rsync(db, dir_obj_with_files, config):
    """Test scanning directories with missing files."""
    connection_pool = ConnectionPool(config)
    connector = connection_pool.get(f"rsync://{FOLDER}/../testdata/")
    dir_url = f"rsync:///{FOLDER}/../testdata/pub/fedora/linux"
    scan_result = {
        f"{dir_url}/{filename}": fileinfo for filename, fileinfo in dir_obj_with_files.files.items()
    }
    for fileinfo in scan_result.values():
        fileinfo["mode"] = "f"
    connector._scan_result = scan_result
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result is True


def test_scan_missing_files_rsync(db, dir_obj_with_files, config):
    """Test scanning directories with missing files."""
    connection_pool = ConnectionPool(config)
    connector = connection_pool.get(f"rsync://{FOLDER}/../testdata/")
    dir_url = f"rsync:///{FOLDER}/../testdata/pub/fedora/linux"
    connector._scan_result = connector._run(dir_url)
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result is False


def test_scan_empty_directory_rsync(db, dir_obj):
    """Test scanning empty directories with rsync"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get(f"rsync://{FOLDER}/../testdata/")
    dir_url = f"rsync://{FOLDER}/../testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj)
    assert result is True


def test_scan_http(db, dir_obj_with_files):
    """Test scanning directories with http"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    mocked_connection = object()
    connector.get_connection = Mock(return_value=mocked_connection)
    connector._check_file = Mock(return_value=True)
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result is True
    connector.get_connection.assert_called_once()
    connector._check_file.assert_called_once_with(
        mocked_connection, f"{dir_url}/does-not-exist", {"size": 1, "stat": 1}, True
    )


def test_scan_missing_files_http(db, dir_obj_with_files):
    """Test scanning empty directories with http"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    mocked_connection = object()
    connector.get_connection = Mock(return_value=mocked_connection)
    connector._check_file = Mock(return_value=False)
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result is False
    connector.get_connection.assert_called_once()
    connector._check_file.assert_called_once_with(
        mocked_connection, f"{dir_url}/does-not-exist", {"size": 1, "stat": 1}, True
    )


def test_scan_empty_directory_http(db, dir_obj):
    """Test scanning empty directories with http"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    connector.get_connection = Mock()
    connector._check_file = Mock(return_value=True)
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj)
    assert result is True
    connector.get_connection.assert_called_once()
    connector._check_file.assert_not_called()


def test_scan_ftp(db, dir_obj_with_files):
    """Test scanning directories with ftp"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("ftp://localhost/testdata/")
    connector.get_ftp_dir = Mock(return_value=dir_obj_with_files.files)
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result is True
    connector.get_ftp_dir.assert_called_once_with(dir_url, True)


def test_scan_missing_files_ftp(db, dir_obj_with_files):
    """Test scanning empty directories with ftp"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("ftp://localhost/testdata/")
    connector.get_ftp_dir = Mock(return_value={})
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result is False
    connector.get_ftp_dir.assert_called_once_with(dir_url, True)


def test_scan_empty_directory_ftp(db, dir_obj):
    """Test scanning empty directories with ftp"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("ftp://localhost/testdata/")
    connector.get_ftp_dir = Mock(return_value={})
    dir_url = "ftp://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj)
    assert result is True
    connector.get_ftp_dir.assert_called_once_with(dir_url, True)


def test_reporter_host_disabled(config, db, site, hosts):
    failed_host: model.Host = db.scalar(
        sa.select(model.Host).where(model.Host.name == "mirror2.localhost")
    )
    assert failed_host.user_active is True
    crawl_result = CrawlResult(
        host_id=failed_host.id,
        host_name=failed_host.name,
        status=CrawlStatus.DISABLE.value,
        details="dummy crawl failure",
        finished_at=datetime.now(),
        duration=42,
    )
    with mock_sends(HostCrawlerDisabledV1):
        store_crawl_result(
            config,
            options={"repodata": False, "canary": False},
            session=db,
            crawl_result=crawl_result,
        )
    db.refresh(failed_host)
    assert failed_host.user_active is False
    assert failed_host.disable_reason == "dummy crawl failure"


def _http_response(status_code, headers=None, url="http://localhost/testdata/repomd.xml"):
    response = requests.Response()
    response.status_code = status_code
    response.url = url
    response.headers.update(headers or {})
    return response


@pytest.mark.parametrize(
    "headers",
    [
        # Apache and nginx answer a redirect with a short body, so the
        # Content-Length of the redirect page is the one which is returned.
        {"Location": "https://localhost/testdata/repomd.xml", "Content-Length": "169"},
        # Without a Content-Length the check used to report the file as
        # present without ever looking at it.
        {"Location": "https://localhost/testdata/repomd.xml"},
    ],
    ids=["with-content-length", "without-content-length"],
)
def test_scan_http_does_not_follow_redirect(db, headers):
    """A host which redirects does not serve the content on the registered URL"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    conn = Mock(head=Mock(return_value=_http_response(301, headers)))
    url = "http://localhost/testdata/repomd.xml"

    assert connector._check_file(conn, url, {"size": 1, "stat": 1}, True) is False
    # Also when there is nothing to compare the file against.
    assert connector._check_file(conn, url, None, True) is False


def test_check_url_asks_for_the_directory_with_a_slash(db):
    """A directory is asked for with a trailing slash, so it is not redirected

    Servers behind TLS termination which ignore X-Forwarded-Proto build that
    redirect with the wrong scheme, which used to look like the mirror was
    refusing the scheme it registered.
    """
    connection_pool = ConnectionPool({})
    url = "https://localhost/pub/fedora/linux"
    connector = connection_pool.get(url)
    conn = Mock(head=Mock(return_value=_http_response(200, url=f"{url}/")))
    connector.get_connection = Mock(return_value=conn)

    assert connector.check_url(url) is True
    assert conn.head.call_args.args[0] == f"{url}/"
    # An URL which already ends with a slash is left alone.
    connector.check_url(f"{url}/")
    assert conn.head.call_args.args[0] == f"{url}/"


@pytest.mark.parametrize(
    "code, expected",
    [
        (200, True),
        # The directory is there, the server just does not list it.
        (403, True),
        # The server cannot build the listing but does serve the files below.
        (502, True),
        (500, True),
        # These are the mirrors which dropped the content.
        (404, False),
        (410, False),
    ],
)
def test_check_url_accepts_a_directory_which_is_not_listable(db, code, expected):
    """Only a 404 means the mirror dropped the content"""
    connection_pool = ConnectionPool({})
    url = "http://localhost/pub/epel"
    connector = connection_pool.get(url)
    response = _http_response(code, url=f"{url}/")
    connector.get_connection = Mock(return_value=Mock(head=Mock(return_value=response)))

    assert connector.check_url(url) is expected


def test_check_url_does_not_follow_redirect(db):
    """A redirecting base URL is not a working base URL"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    headers = {"Location": "https://localhost/testdata/"}
    response = _http_response(301, headers, url="http://localhost/testdata/")
    # check_url() appends the slash itself, so this is the URL it asks for.
    # A redirect is below 400, so requests considers the response to be ok.
    assert response.ok is True
    connector.get_connection = Mock(return_value=Mock(head=Mock(return_value=response)))

    assert connector.check_url("http://localhost/testdata/") is False


def test_get_file_does_not_end_up_on_another_scheme(db):
    """Fetching a file over http does not end up on https"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    url = "http://localhost/testdata/repomd.xml"
    # requests follows redirects on GET, so the response is the one from the
    # https URL and the http request is in the history.
    followed = _http_response(200, url="https://localhost/testdata/repomd.xml")
    followed.history = [_http_response(301, url=url)]
    connector.get_connection = Mock(return_value=Mock(get=Mock(return_value=followed)))

    with pytest.raises(FetchingFailed):
        connector._get_file(url)


def test_get_file_allows_a_redirect_on_the_same_scheme(db):
    """Being sent somewhere else over the same scheme is fine"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    url = "http://localhost/testdata/repomd.xml"
    followed = _http_response(200, url="http://localhost/testdata/moved/repomd.xml")
    followed.history = [_http_response(301, url=url)]
    followed._content = b"repomd"
    connector.get_connection = Mock(return_value=Mock(get=Mock(return_value=followed)))

    assert connector._get_file(url) == b"repomd"


@pytest.mark.parametrize(
    "url, location",
    [
        # The usual case: a directory without a trailing slash is answered
        # with a redirect to the same URL with one.
        (
            "http://localhost/pub/Mirrors/alt.fedoraproject.org",
            "http://localhost/pub/Mirrors/alt.fedoraproject.org/",
        ),
        # The same, with a relative Location header.
        ("http://localhost/pub/fedora", "/pub/fedora/"),
        # https mirrors do this too.
        ("https://localhost/pub/fedora", "https://localhost/pub/fedora/"),
    ],
    ids=["absolute", "relative", "https"],
)
def test_redirect_on_the_same_scheme_is_not_a_problem(db, url, location):
    """A trailing slash redirect does not make a mirror fail"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get(url)
    response = _http_response(301, {"Location": location}, url=url)
    connector.get_connection = Mock(return_value=Mock(head=Mock(return_value=response)))

    # The base directory check has to keep accepting these, every common web
    # server answers a directory this way.
    assert connector.check_url(url) is True
