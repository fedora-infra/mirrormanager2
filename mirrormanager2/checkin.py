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
MirrorManager2 xmlrpc controller.
'''

import base64
import pickle
import json
import bz2
import logging
import zlib

import flask
from flaskext.xmlrpc import XMLRPCHandler, Fault

from mirrormanager2.app import APP, ADMIN, SESSION
from mirrormanager2.lib import model
from mirrormanager2.lib.hostconfig import read_host_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@APP.route('/checkin/json', methods=['POST'])
def checkin_json():
    ctype = flask.request.headers.get('Content-Type')
    try:
        if ctype == 'application/gzip':
            data = json.loads(zlib.decompress(flask.request.data, 16+zlib.MAX_WBITS))
        elif ctype == 'application/json':
            data = json.loads(flask.request.data)
        else:
            return 'Invalid content type', 415
    except Exception as ex:
        logging.error('Unable to read input data: %s' % ex)
        return 'Error decoding', 400

    try:
        r, message = read_host_config(SESSION, config)
    except Exception as ex:
        logging.error('Unable to parse input data: %s' % ex)
        return 'Error parsing', 500

    if r is not None:
        logging.info('JSON checkin succesful: %s' % message)
        return message
    else:
        logging.error('Error during JSON checkin: %s' % message)
        return message, 406


XMLRPC = XMLRPCHandler('xmlrpc')
XMLRPC.connect(APP, '/xmlrpc')


@XMLRPC.register
def checkin(pickledata):
    uncompressed = bz2.decompress(base64.urlsafe_b64decode(pickledata))
    try:
        config = json.loads(uncompressed)
    except ValueError:
        logging.info("Fell back to pickle")
        config = pickle.loads(uncompressed)
    r, message = read_host_config(SESSION, config)
    if r is not None:
        logging.info("Checkin succesful: %s" % message)
        return message + 'checked in successful'
    else:
        logging.error("Error during checkin: %s" % message)
        return message + 'error checking in'
