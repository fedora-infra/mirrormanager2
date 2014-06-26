# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
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
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
MirrorManager2 internal api to manage sync.
'''

import subprocess
import tempfile


def run_rsync(rsyncpath, extra_rsync_args=None):
    tmpfile = tempfile.SpooledTemporaryFile()
    cmd = "rsync --temp-dir=/tmp -r --exclude=.snapshot --exclude='*.~tmp~'"
    if extra_rsync_args is not None:
        cmd += ' ' + extra_rsync_args
    cmd += ' ' + rsyncpath
    devnull = open('/dev/null', 'r+')
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdin=devnull,
        stdout=tmpfile,
        stderr=devnull,
        close_fds=True,
        bufsize=-1
    )
    p.wait()
    result = p.returncode
    tmpfile.flush()
    tmpfile.seek(0)
    return (result, tmpfile)
