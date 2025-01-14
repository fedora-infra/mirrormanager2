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
from unittest.mock import Mock

import pytest

from mirrormanager2 import default_config
from mirrormanager2.crawler.connection_pool import ConnectionPool
from mirrormanager2.lib import model
from mirrormanager2.lib.sync import run_rsync

FOLDER = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def config():
    config = dict()
    for key in dir(default_config):
        if key.isupper():
            config[key] = getattr(default_config, key)
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


def test_scan_ftp(db, dir_obj_with_files):
    """Test scanning directories with ftp"""
    connection_pool = ConnectionPool({})
    connector = connection_pool.get("ftp://localhost/testdata/")
    connector.get_ftp_dir = Mock(return_value=dir_obj_with_files.files)
    dir_url = "http://localhost/testdata/pub/fedora/linux"
    result = connector.check_dir(dir_url, dir_obj_with_files)
    assert result is True
    connector.get_ftp_dir.assert_called_once_with(dir_url, True)
