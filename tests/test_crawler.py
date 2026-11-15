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
from mirrormanager2.crawler import crawler as crawler_module
from mirrormanager2.crawler.connection_pool import ConnectionPool
from mirrormanager2.crawler.connector import FetchingFailed
from mirrormanager2.crawler.crawler import (
    Crawler,
    CrawlResult,
    _hcd_path,
    decide_dir_only_statuses,
    worker,
)
from mirrormanager2.crawler.reporter import store_crawl_result
from mirrormanager2.crawler.states import CrawlStatus, DirStatus, SyncStatus
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


@pytest.mark.parametrize(
    "payload",
    [
        ";touch {marker}",
        "$(touch {marker})",
        "`touch {marker}`",
        "|| touch {marker}",
        "| touch {marker}",
    ],
)
def test_run_rsync_shell_injection(tmp_path, payload):
    # Regression test to ensure shell metacharacters in rsync path are not executed
    marker = tmp_path / "marker"
    malicious_path = f"rsync://localhost/testdata/{payload.format(marker=marker)}"

    result, fd = run_rsync(malicious_path)
    fd.close()

    # The command should fail (non-zero exit code) because the path is invalid
    assert result != 0
    # The shell injection must fail, meaning the marker file was never created
    assert not marker.exists()


def test_run_rsync_extra_args_quoting():
    # Regression test to ensure quoting in extra_rsync_args is handled correctly
    dest = FOLDER + "/../testdata/"
    extra = "--exclude '*aalib*'"

    result, fd = run_rsync(dest, extra)
    assert result == 0

    output = ""
    while True:
        line = fd.readline()
        if not line:
            break
        output += line

    fd.close()

    # Check that aalib is correctly excluded despite the quoting
    assert "aalib" not in output
    # Check that non-excluded files remain
    assert "fedora/linux/development/22/" in output


def test_scan_rsync(db, dir_obj_with_files, config):
    """Test scanning directories whose files all match."""
    connection_pool = ConnectionPool(config)
    connector = connection_pool.get(f"rsync://{FOLDER}/../testdata/")
    dirname = "pub/fedora/linux"
    scan_result = {
        f"{dirname}/{filename}": fileinfo for filename, fileinfo in dir_obj_with_files.files.items()
    }
    for fileinfo in scan_result.values():
        fileinfo["mode"] = "f"
    scan_result[dirname] = {"mode": "drwxr-xr-x", "size": "4096", "date": "", "time": ""}
    connector._scan_result = scan_result
    result = connector.check_dir(dirname, dir_obj_with_files)
    assert result == DirStatus.UP2DATE


def test_scan_missing_files_rsync(db, dir_obj_with_files, config):
    """A directory which exists on the mirror but misses files is stale."""
    connection_pool = ConnectionPool(config)
    connector = connection_pool.get(f"rsync://{FOLDER}/../testdata/")
    connector._scan_result = connector._run(f"{FOLDER}/../testdata/")
    # The directory itself is in the listing, the files of dir_obj_with_files
    # are not.
    result = connector.check_dir("pub/fedora/linux", dir_obj_with_files)
    assert result == DirStatus.STALE


def test_scan_missing_directory_rsync(db, dir_obj_with_files, config):
    """A directory which is not in the listing does not exist on the mirror."""
    connection_pool = ConnectionPool(config)
    connector = connection_pool.get(f"rsync://{FOLDER}/../testdata/")
    connector._scan_result = connector._run(f"{FOLDER}/../testdata/")
    result = connector.check_dir("pub/fedora/linux/releases/21", dir_obj_with_files)
    assert result == DirStatus.ABSENT


def test_scan_empty_directory_rsync(db, dir_obj, config):
    """A directory without files which the mirror carries is present."""
    connection_pool = ConnectionPool(config)
    connector = connection_pool.get(f"rsync://{FOLDER}/../testdata/")
    connector._scan_result = connector._run(f"{FOLDER}/../testdata/")
    result = connector.check_dir("pub/fedora/linux", dir_obj)
    assert result == DirStatus.PRESENT


def test_scan_empty_missing_directory_rsync(db, dir_obj, config):
    """A directory without files which the mirror does not carry is absent."""
    connection_pool = ConnectionPool(config)
    connector = connection_pool.get(f"rsync://{FOLDER}/../testdata/")
    connector._scan_result = connector._run(f"{FOLDER}/../testdata/")
    result = connector.check_dir("pub/fedora/linux/releases/21", dir_obj)
    assert result == DirStatus.ABSENT


def test_scan_http(db, dir_obj_with_files):
    """Test scanning directories with http"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    mocked_connection = object()
    connector.get_connection = Mock(return_value=mocked_connection)
    connector._check_file = Mock(return_value=True)
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result == DirStatus.UP2DATE
    connector.get_connection.assert_called_once()
    connector._check_file.assert_called_once_with(
        mocked_connection, f"{dir_url}/does-not-exist", {"size": 1, "stat": 1}, True
    )


@pytest.mark.parametrize(
    "dir_code, expected",
    [
        # The directory answers, so the mirror carries it with old content.
        (200, DirStatus.STALE),
        (403, DirStatus.STALE),
        # The directory itself is gone, the mirror does not carry it.
        (404, DirStatus.ABSENT),
    ],
)
def test_scan_missing_files_http(db, dir_obj_with_files, dir_code, expected):
    """A failed file check asks the directory itself to tell stale from absent."""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    mocked_connection = Mock(head=Mock(return_value=_http_response(dir_code, url=f"{dir_url}/")))
    connector.get_connection = Mock(return_value=mocked_connection)
    connector._check_file = Mock(return_value=False)
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result == expected
    connector.get_connection.assert_called_once()
    connector._check_file.assert_called_once_with(
        mocked_connection, f"{dir_url}/does-not-exist", {"size": 1, "stat": 1}, True
    )
    # The tie-breaker request asks for the directory with a trailing slash.
    mocked_connection.head.assert_called_once()
    assert mocked_connection.head.call_args.args[0] == f"{dir_url}/"


@pytest.mark.parametrize(
    "dir_code, expected",
    [
        (200, DirStatus.PRESENT),
        # The directory is there, the server just does not list it.
        (403, DirStatus.PRESENT),
        (404, DirStatus.ABSENT),
        (410, DirStatus.ABSENT),
    ],
)
def test_scan_empty_directory_http(db, dir_obj, dir_code, expected):
    """A directory without files is checked for existence, not content."""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("http://localhost/testdata/")
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    mocked_connection = Mock(head=Mock(return_value=_http_response(dir_code, url=f"{dir_url}/")))
    connector.get_connection = Mock(return_value=mocked_connection)
    connector._check_file = Mock(return_value=True)
    result = connector.check_dir(dir_url, dir_obj)
    assert result == expected
    connector.get_connection.assert_called_once()
    connector._check_file.assert_not_called()
    assert mocked_connection.head.call_args.args[0] == f"{dir_url}/"


def test_scan_ftp(db, dir_obj_with_files):
    """Test scanning directories with ftp"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("ftp://localhost/testdata/")
    connector.get_ftp_dir = Mock(return_value=dir_obj_with_files.files)
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result == DirStatus.UP2DATE
    connector.get_ftp_dir.assert_called_once_with(dir_url, True)


def test_scan_missing_files_ftp(db, dir_obj_with_files):
    """A directory which lists but misses files is stale."""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("ftp://localhost/testdata/")
    connector.get_ftp_dir = Mock(return_value={})
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result == DirStatus.STALE
    connector.get_ftp_dir.assert_called_once_with(dir_url, True)


def test_scan_missing_directory_ftp(db, dir_obj_with_files):
    """A directory the server reports as nonexistent is absent."""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("ftp://localhost/testdata/")
    connector.get_ftp_dir = Mock(return_value=DirStatus.ABSENT)
    dir_url = "ftp://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result == DirStatus.ABSENT
    connector.get_ftp_dir.assert_called_once_with(dir_url, True)


def test_scan_empty_directory_ftp(db, dir_obj):
    """A directory without files which the mirror carries is present."""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("ftp://localhost/testdata/")
    connector.get_ftp_dir = Mock(return_value={})
    dir_url = "ftp://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj)
    assert result == DirStatus.PRESENT
    connector.get_ftp_dir.assert_called_once_with(dir_url, True)


def test_decide_dir_only_partial_mirror():
    """A mirror which excludes a part of the tree stays up to date."""
    master_paths = {
        "",
        "development",
        "development/rawhide",
        "development/rawhide/x86_64",
        "development/rawhide/ppc64le",
    }
    # The mirror excludes ppc64le, so that path has no HostCategoryDir.
    statuses = {"development/rawhide/x86_64": True}
    pending = {"development": 1, "development/rawhide": 2}
    decisions = decide_dir_only_statuses(pending, statuses, master_paths)
    assert decisions == {"development": True, "development/rawhide": True}


def test_decide_dir_only_stale_child():
    """A stale child makes every directory above it stale."""
    master_paths = {
        "",
        "development",
        "development/rawhide",
        "development/rawhide/x86_64",
    }
    statuses = {"development/rawhide/x86_64": False}
    pending = {"development": 1, "development/rawhide": 2}
    decisions = decide_dir_only_statuses(pending, statuses, master_paths)
    assert decisions == {"development": False, "development/rawhide": False}


def test_decide_dir_only_empty_shell():
    """A directory whose content below is all excluded is not up to date."""
    master_paths = {"", "development", "development/rawhide"}
    statuses = {}
    pending = {"development": 1}
    decisions = decide_dir_only_statuses(pending, statuses, master_paths)
    assert decisions == {"development": False}


def test_decide_dir_only_master_leaf():
    """A directory which is empty on the master too is up to date."""
    master_paths = {"", "empty"}
    statuses = {}
    pending = {"empty": 1}
    decisions = decide_dir_only_statuses(pending, statuses, master_paths)
    assert decisions == {"empty": True}


def test_decide_dir_only_topdir_chain():
    """The decision runs bottom-up through nested directories without files."""
    master_paths = {"", "development", "development/rawhide", "development/rawhide/x86_64"}
    statuses = {"development/rawhide/x86_64": True}
    pending = {"": 1, "development": 2, "development/rawhide": 3}
    decisions = decide_dir_only_statuses(pending, statuses, master_paths)
    assert decisions == {"": True, "development": True, "development/rawhide": True}


@pytest.mark.parametrize(
    "topname,dirname,expected",
    [
        ("pub/fedora/linux", "pub/fedora/linux/releases/26", "releases/26"),
        ("pub/fedora/linux", "pub/fedora/linux", ""),
        ("", "releases/26", "releases/26"),
    ],
)
def test_hcd_path(topname, dirname, expected):
    """The path has no leading slash, also for an empty top directory."""
    assert _hcd_path(topname, dirname) == expected


@pytest.fixture()
def crawler_obj(config, db, base_items, site, hosts, directory, category, hostcategory):
    host = db.get(model.Host, 2)
    options = {"debug": False, "host_timeout": 600}
    return Crawler(config, db, options, Mock(), host)


@pytest.fixture()
def crawled_hc_and_dir(db):
    # HostCategory 3 belongs to host 2 and the "Fedora Linux" category, whose
    # topdir is "pub/fedora/linux" (directory 1). Directory 4 is
    # "pub/fedora/linux/releases/26".
    hc = db.get(model.HostCategory, 3)
    dir_obj = db.get(model.Directory, 4)
    return hc, dir_obj


def test_sync_dir_absent_deletes_hcd(db, crawler_obj, crawled_hc_and_dir):
    """A directory the mirror does not carry loses its HostCategoryDir."""
    hc, dir_obj = crawled_hc_and_dir
    path = _hcd_path(hc.category.topdir.name, dir_obj.name)
    db.add(
        model.HostCategoryDir(
            host_category_id=hc.id, directory_id=dir_obj.id, path=path, up2date=False
        )
    )
    db.commit()
    sync_status, hcd_id, up2date = crawler_obj.sync_dir(hc, dir_obj, DirStatus.ABSENT, path)
    assert sync_status == SyncStatus.DELETED
    assert hcd_id is None
    db.commit()
    assert (
        db.query(model.HostCategoryDir).filter_by(host_category_id=hc.id, path=path).first() is None
    )


def test_sync_dir_absent_without_hcd(db, crawler_obj, crawled_hc_and_dir):
    """An absent directory which never had a HostCategoryDir does not get one."""
    hc, dir_obj = crawled_hc_and_dir
    path = _hcd_path(hc.category.topdir.name, dir_obj.name)
    sync_status, hcd_id, up2date = crawler_obj.sync_dir(hc, dir_obj, DirStatus.ABSENT, path)
    assert sync_status == SyncStatus.UNKNOWN
    assert hcd_id is None
    db.commit()
    assert (
        db.query(model.HostCategoryDir).filter_by(host_category_id=hc.id, path=path).first() is None
    )


def test_sync_dir_stale_does_not_create_hcd(db, crawler_obj, crawled_hc_and_dir):
    """A stale directory which never had a HostCategoryDir does not get one."""
    hc, dir_obj = crawled_hc_and_dir
    path = _hcd_path(hc.category.topdir.name, dir_obj.name)
    sync_status, hcd_id, up2date = crawler_obj.sync_dir(hc, dir_obj, DirStatus.STALE, path)
    assert sync_status == SyncStatus.UNKNOWN
    assert hcd_id is None
    db.commit()
    assert (
        db.query(model.HostCategoryDir).filter_by(host_category_id=hc.id, path=path).first() is None
    )


def test_sync_dir_stale_marks_existing_hcd(db, crawler_obj, crawled_hc_and_dir):
    """A stale directory keeps its HostCategoryDir with up2date False."""
    hc, dir_obj = crawled_hc_and_dir
    path = _hcd_path(hc.category.topdir.name, dir_obj.name)
    db.add(
        model.HostCategoryDir(
            host_category_id=hc.id, directory_id=dir_obj.id, path=path, up2date=True
        )
    )
    db.commit()
    sync_status, hcd_id, up2date = crawler_obj.sync_dir(hc, dir_obj, DirStatus.STALE, path)
    assert sync_status == SyncStatus.NOT_UP2DATE
    assert hcd_id is not None
    assert up2date is False
    db.commit()
    hcd = db.query(model.HostCategoryDir).filter_by(host_category_id=hc.id, path=path).one()
    assert hcd.up2date is False


def test_sync_dir_present_defers_decision(db, crawler_obj, crawled_hc_and_dir):
    """A directory without files keeps its stored value until the post-pass."""
    hc, dir_obj = crawled_hc_and_dir
    path = _hcd_path(hc.category.topdir.name, dir_obj.name)
    db.add(
        model.HostCategoryDir(
            host_category_id=hc.id, directory_id=dir_obj.id, path=path, up2date=False
        )
    )
    db.commit()
    sync_status, hcd_id, up2date = crawler_obj.sync_dir(hc, dir_obj, DirStatus.PRESENT, path)
    assert hcd_id is not None
    assert up2date is False
    hcd = db.query(model.HostCategoryDir).filter_by(host_category_id=hc.id, path=path).one()
    assert hcd.up2date is False


def test_sync_dir_only_dirs_updates_rows(db, crawler_obj, crawled_hc_and_dir):
    """The post-pass writes the decided values to the HostCategoryDirs."""
    from mirrormanager2.crawler.crawler import CrawlStats

    hc, dir_obj = crawled_hc_and_dir
    hcd = model.HostCategoryDir(
        host_category_id=hc.id, directory_id=dir_obj.id, path="releases", up2date=True
    )
    db.add(hcd)
    db.commit()
    stats = CrawlStats()
    crawler_obj._sync_dir_only_dirs(
        pending={"releases": hcd.id},
        statuses={"releases": True, "releases/26": False},
        master_paths={"", "releases", "releases/26"},
        stats=stats,
    )
    db.commit()
    db.refresh(hcd)
    assert hcd.up2date is False
    assert stats.not_up2date == 1


def test_scan_host_category_repairs_paths_with_a_slash(
    config, db, base_items, site, hosts, directory, category, hostcategory, monkeypatch
):
    """The scan keeps one row per directory, the crawler's, without the slash."""
    options = {"debug": False, "host_timeout": 600, "canary": False, "repodata": False}
    crawler = Crawler(config, db, options, Mock(), db.get(model.Host, 2))
    crawler.timeout.start()
    hc, dir_obj = db.get(model.HostCategory, 3), db.get(model.Directory, 4)
    crawler_row = model.HostCategoryDir(
        host_category_id=hc.id, directory_id=dir_obj.id, path="/releases/26", up2date=False
    )
    old_row = model.HostCategoryDir(
        host_category_id=hc.id, directory_id=dir_obj.id, path="releases/26", up2date=False
    )
    db.add_all([crawler_row, old_row])
    db.commit()
    crawler_row_id = crawler_row.id
    monkeypatch.setattr(
        crawler, "_get_directory_statuses", lambda hc: [(dir_obj, DirStatus.UP2DATE)]
    )

    crawler._scan_host_category(hc)

    rows = db.query(model.HostCategoryDir).filter_by(host_category_id=hc.id).all()
    assert [(row.id, row.path, row.up2date) for row in rows] == [
        (crawler_row_id, "releases/26", True)
    ]


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


def test_reporter_host_deleted_during_crawl(config, db, site, hosts, caplog):
    """A host deleted while the crawl was running must not break storing the results."""
    deleted_host: model.Host = db.scalar(
        sa.select(model.Host).where(model.Host.name == "mirror2.localhost")
    )
    deleted_host_id = deleted_host.id
    crawl_result = CrawlResult(
        host_id=deleted_host_id,
        host_name=deleted_host.name,
        status=CrawlStatus.OK.value,
        details=None,
        finished_at=datetime.now(),
        duration=42,
    )
    db.delete(deleted_host)
    db.commit()
    store_crawl_result(
        config,
        options={"repodata": False, "canary": False},
        session=db,
        crawl_result=crawl_result,
    )
    assert f"Host {deleted_host_id} (mirror2.localhost) no longer exists" in caplog.text


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


def test_rsync_listing_not_reused_across_categories(db, dir_obj_with_files, config):
    """One rsync module serving several categories: the listing must be redone per category URL."""
    from mirrormanager2.crawler.rsync_connector import RsyncConnector

    connector = RsyncConnector(config, "localhost", 0, lambda *a: None)
    listings = []

    def fake_run(url):
        listings.append(url)
        return {"dummy": {"mode": "-rw-r--r--", "size": "1", "date": "", "time": ""}}

    connector._run = fake_run
    connector._check_dir = lambda dirname, directory: True
    connector.check_category("rsync://localhost/module/free/fedora", dir_obj_with_files, 0)
    connector.check_category("rsync://localhost/module/free/fedora", dir_obj_with_files, 0)
    assert listings == ["rsync://localhost/module/free/fedora"]
    connector.check_category("rsync://localhost/module/free/el", dir_obj_with_files, 0)
    assert listings == [
        "rsync://localhost/module/free/fedora",
        "rsync://localhost/module/free/el",
    ]


def test_reporter_host_disabled_without_fedora_messaging(config, db, site, hosts, monkeypatch):
    """USE_FEDORA_MESSAGING = False must disable the host without touching the message bus."""
    from mirrormanager2.crawler import notif

    def fail(*args, **kwargs):
        raise AssertionError("fedmsg_publish must not be called")

    monkeypatch.setattr(notif, "fedmsg_publish", fail)
    config["USE_FEDORA_MESSAGING"] = False
    failed_host: model.Host = db.scalar(
        sa.select(model.Host).where(model.Host.name == "mirror2.localhost")
    )
    crawl_result = CrawlResult(
        host_id=failed_host.id,
        host_name=failed_host.name,
        status=CrawlStatus.DISABLE.value,
        details="dummy crawl failure",
        finished_at=datetime.now(),
        duration=42,
    )
    store_crawl_result(
        config,
        options={"repodata": False, "canary": False},
        session=db,
        crawl_result=crawl_result,
    )
    db.refresh(failed_host)
    assert failed_host.user_active is False


@pytest.mark.parametrize(
    "host_name,crawled",
    [
        ("private.localhost", False),
        ("mirror.localhost", True),
    ],
)
def test_worker_skips_private_hosts(
    config, db, db_url, site, hosts, monkeypatch, host_name, crawled
):
    """A host which is private when its worker runs must not be crawled."""
    config["SQLALCHEMY_DATABASE_URI"] = db_url
    host = db.scalar(sa.select(model.Host).where(model.Host.name == host_name))
    crawler_class = Mock()
    monkeypatch.setattr(crawler_module, "Crawler", crawler_class)
    monkeypatch.setattr(crawler_module, "crawl_and_report", Mock(return_value="crawled"))

    result = worker({}, config, Mock(), host.id)

    assert crawler_class.called is crawled
    assert result == ("crawled" if crawled else None)
