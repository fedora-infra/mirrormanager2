# -*- coding: utf-8 -*-
#
# Copyright © 2015  Red Hat, Inc.
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
MirrorManager2 API controller.
'''

import flask

import mirrormanager2.lib as mmlib
from mirrormanager2.app import APP, SESSION


@APP.route('/api/mirroradmins/')
@APP.route('/api/mirroradmins')
def api_mirroradmins():
    '''
    List the admins of a mirror
    ---------------------------
    Returns all the mirror admins or the admins of a specific mirror
    specified by its host URL or site name.

    ::

        /api/mirroradmins/

        /api/mirroradmins/?name=<mirror url>

    Accepts GET queries only.

    :kwarg name: restrict the list of admins returns to the admins of this
        mirror or host.

    Sample response:

    ::

      {
        "admins": [
          'foo',
          'bar',
        ],
        "total": 2
      }

    '''

    name = flask.request.args.get('name', None)
    if not name:
        admins = set(
            [admin.username
             for admin in mmlib.get_siteadmins(SESSION)]
        )
    else:
        site = None
        host = mmlib.get_host_by_name(SESSION, name)
        if not host:
            site = mmlib.get_site_by_name(SESSION, name)
        else:
            site = host.site

        if not site:
            jsonout = flask.jsonify(
                {'message': 'No host or site found for %s' % name})
            jsonout.status_code = 400
            return jsonout

        admins = set([site.created_by])
        for admin in site.admins:
            admins.add(admin.username)

    output = {
        'total': len(admins),
        'admins': list(admins),
    }

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout


@APP.route('/api/repositories/')
@APP.route('/api/repositories')
def api_repositories():
    '''
    List the repositories
    ---------------------
    Returns the list of repositories present in the database.

    ::

        /api/repositories

    Accepts GET queries only.

    Sample response:

    ::

      {
        "repositories": [
          {
            "fedora-install-20": {
              "directory": "pub/fedora/linux/releases/20/Fedora/i386/os",
              "name": "pub/fedora/linux/releases/20/Fedora/i386/os"
            }
          },
          {
            "rawhide": {
              "directory": "pub/fedora/linux/development/rawhide/i386/os",
              "name": "Fedora-Fedora Linux-development-i386"
            }
          }
        ]
        "total": 2
      }

    '''

    repositories = mmlib.get_repositories(SESSION)
    repos = []
    for repository in repositories:
        if not repository:
            continue

        tmp = {
            'name': repository.name,
            'directory': repository.directory.name,
        }
        repos.append({repository.prefix: tmp})

    output = {
        'total': len(repositories),
        'repositories': repos,
    }

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout
