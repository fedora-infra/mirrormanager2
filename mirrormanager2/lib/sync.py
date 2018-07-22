# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
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
import errno
import threading


def check_timeout(logger, p, timeout, e):
    """
    Check if the process is running and kill it if it running
    longer than the specified timeout.

    :param logger: If a logger is available it will be used for messages
    :param p: The process handle representing the rsync process
    :param timeout: The timeout after which the rsync process should
                    definitely end. Will be p.kill()-ed.
    :param e: The threading.Event() object used to wait for the end of
              rsync process
    """

    e.wait(timeout)

    if p.poll() is None:
        try:
            p.kill()
            if logger:
                logger.info(
                    'Error: process taking too long to complete - terminated'
                )
        except OSError as err:
            if err.errno != errno.ESRCH:
                # if there is such process
                raise


def run_rsync(rsyncpath, extra_rsync_args=None, logger=None, timeout=None):
    """
    This functions runs 'rsync' on :rsyncpath: and returns the output listing
    as a file descriptor pointing to a tempfile.SpooledTemporaryFile().
    It is used in the crawler and umdl and aborts after :timeout: if specified.

    :param rsyncpath: The path 'rsync' should use to do a recursive listing.
                      This can be anything 'rsync' accepts.
    :param extra_rsync_args: Additional parameters added to 'rsync' like
                             excludes or includes or anything else.
    :param logger: If a logger is available it will be used for messages
    :param timeout: The timeout after which the rsync process should
                    definitely end. Will be p.kill()-ed.
    :returns: return code, file descriptor
    """

    tmpfile = tempfile.SpooledTemporaryFile(mode='w+t')
    cmd = "rsync --temp-dir=/tmp -r --exclude=.snapshot --exclude='*.~tmp~'"
    if extra_rsync_args is not None:
        cmd += ' ' + extra_rsync_args
    cmd += ' ' + rsyncpath
    if logger is not None:
        logger.info("About to run following rsync command: " + cmd)
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

    timeout_thread = None
    e = None
    if timeout:
        # Start a thread to check the status of the process after ``timeout``
        # seconds. If the process is still running then, kill it.
        e = threading.Event()
        timeout_thread = threading.Thread(
            target=check_timeout,
            args=[logger, p, timeout, e]
        )
        timeout_thread.start()

    p.wait()

    if e:
        e.set()
        timeout_thread.join()

    result = p.returncode

    tmpfile.flush()
    tmpfile.seek(0)
    return (result, tmpfile)
