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
MirrorManager2 internal api to manage PID.
'''

import os


def remove_pidfile(pidfile):
    os.unlink(pidfile)


def create_pidfile_dir(pidfile):
    piddir = os.path.dirname(pidfile)
    if piddir and not os.path.exists(piddir):
        os.makedirs(piddir, mode=0o755)


def write_pidfile(pidfile, pid):
    create_pidfile_dir(pidfile)
    with open(pidfile, 'w') as stream:
        stream.write(str(pid)+'\n')
    return 0


def manage_pidfile(pidfile):
    """returns 1 if another process is running that is named in pidfile,
    otherwise creates/writes pidfile and returns 0."""
    pid = os.getpid()
    if not os.path.exists(pidfile):
        return write_pidfile(pidfile, pid)

    oldpid = ''
    try:
        with open(pidfile, 'r') as stream:
            oldpid = stream.read()
    except IOError as err:
        return 1

    # is the oldpid process still running?
    try:
        os.kill(int(oldpid), 0)
    except ValueError:  # malformed oldpid
        return write_pidfile(pidfile, pid)
    except OSError as err:
        if err.errno == 3:  # No such process
            return write_pidfile(pidfile, pid)
    return 1
