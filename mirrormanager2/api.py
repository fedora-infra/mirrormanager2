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
    Returns the admins of a mirror given a specific URL.

    ::

        /api/mirroradmins/?name=<mirror url>

    Accepts GET queries only.

    :arg name: the url of the mirror to return the admins of.

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
        jsonout = flask.jsonify({'message': 'No name provided'})
        jsonout.status_code = 400
        return jsonout

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
