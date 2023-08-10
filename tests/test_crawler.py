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

'''
mirrormanager2 tests for the crawler.
'''

import os
from mirrormanager2.lib.sync import run_rsync


FOLDER = os.path.dirname(os.path.abspath(__file__))


def test_run_rsync():
    """ Test the run_rsync function"""

    # Test timeout if timeout works

    # Travis needs a really small timeout value
    result, fd = run_rsync('/', timeout=0.05)
    fd.close()
    assert result == -9

    # Test if timeout does not trigger
    result, fd = run_rsync('.', timeout=10)
    fd.close()
    assert result != -9

    # Test with non-existing directory
    result, fd = run_rsync('this-is-not-here-i-hope--')
    fd.close()
    assert result == 23
    assert result != 0

    # Test the 'normal' usage
    dest = FOLDER + "/../testdata/"
    result, fd = run_rsync(dest)
    assert result == 0
    output = ''
    while True:
        line = fd.readline()
        if not line:
            break
        output += line

    fd.close()

    for i in [
            '20/Live/x86_64/Fedora-Live-x86_64-20-CHECKSUM',
            'pub/fedora/linux/releases/20/Fedora/',
            'releases/20/Fedora/source/SRPMS/a/aalib-1.4.0-0.23',
            'pub/fedora/linux/development/22/x86_64/os/repodata'
    ]:
        assert i in output

    # Test the 'extra_rsync_args'
    extra = '--exclude *aalib*'
    result, fd = run_rsync(dest, extra)
    assert result == 0
    output = ''
    while True:
        line = fd.readline()
        if not line:
            break
        output += line

    fd.close()

    # Check that aalib is excluded
    assert 'aalib' not in output

    # Check that non-excluded files are still included
    assert 'fedora/linux/development/22/' in output
