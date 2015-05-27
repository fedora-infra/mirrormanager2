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

        /api/mirroradmins/?url=<mirror url>

    Accepts GET queries only.

    :arg url: the url of the mirror to return the admins of.

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

    url = flask.request.args.get('url', None)
    if not url:
        jsonout = flask.jsonify({'message': 'No url provided'})
        jsonout.status_code = 400
        return jsonout

    host = mmlib.get_host_by_name(mirrormanager2.app.SESSION, url)
    if not host:
        jsonout = flask.jsonify({'message': 'No host found for %s' % url})
        jsonout.status_code = 400
        return jsonout

    admins = set([host.site.created_by])
    for admin in host.site.admins:
        admins.add(admin)

    output = {
        'total': len(admins),
        'admins': list(admins),
    }

    jsonout = flask.jsonify(output)
    jsonout.status_code = 200
    return jsonout
