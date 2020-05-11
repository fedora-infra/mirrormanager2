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
MirrorManager2 Host configuration.
'''

import mirrormanager2.lib

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_config(config):
    message = ''
    if type(config) != dict:
        logging.critical("NON-DICT SUBMITTED: %s" % config)
        message += 'config file is not a dict.\n'\
            'Please update your copy of report_mirror.\n'
        return (False, message)
    if 'version' not in config:
        message += 'config file has no version field.\n'
        return (False, message)
    # this field is an integer
    if config['version'] != 0:
        message += 'config file version is not 0, is %s.\n' % (
            config['version'])
        return (False, message)

    for section in ['global', 'site', 'host']:
        if section not in config:
            message += 'config file missing section %s.\n' % (section)
            return (False, message)

    globl = config['global']
    # this field is a string as it comes from the config file
    if 'enabled' not in globl or globl['enabled'] != '1':
        message += 'config file section [global] not enabled.\n'
        return (False, message)

    site = config['site']
    for opt in ['name', 'password']:
        if opt not in site:
            message += 'config file [site] missing required option %s.'\
                '\n' % (opt)
            return (False, message)

    host = config['host']
    for opt in ['name']:
        if opt not in host:
            message += 'section [host] missing required option %s.\n' % (
                opt)
            return (False, message)

    for category in config.keys():
        if category in ['global', 'site', 'host', 'version', 'stats']:
            continue

        for opt in ['dirtree']:
            if opt not in config[category]:
                message += 'section [%s] missing required option %s.\n' % (
                    category, opt)
                return (False, message)
    return (True, message)


def read_host_config(session, config):
    rc, message = validate_config(config)
    if not rc:
        return (None, '', message + 'Invalid config file provided, please '
                'check your report_mirror.conf.')

    csite = config['site']
    chost = config['host']
    chostname = chost['name']

    site = mirrormanager2.lib.get_site_by_name(session, csite['name'])
    if not site:
        return (
                None,
                chostname,
                'Config file site name or password incorrect.\n'
        )

    if csite['password'] != site.password:
        return (
                None,
                chostname,
                'Config file site name or password incorrect.\n'
        )

    host = None
    for tmp_host in site.hosts:
        if tmp_host.name == chost['name']:
            host = tmp_host
            break

    if not host:
        return (None, chostname, 'Config file host name for site not found.\n')

    if host.private == False:
        return (
                None,
                chostname,
                'Only private mirrors are allowed to use report_mirror.\n'
        )

    # handle the optional arguments
    if 'user_active' in config['host']:
        if config['host']['user_active'] in ['true', '1', 't', 'y', 'yes']:
            host.user_active = True
        else:
            host.user_active = False

    message = mirrormanager2.lib.uploaded_config(session, host, config)
    return (True, chostname, message)
