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

"""
MirrorManager2 xmlrpc controller.
"""

import base64
import bz2
import json
import logging
from xmlrpc.server import SimpleXMLRPCDispatcher

from flask import current_app, request

from mirrormanager2.database import DB
from mirrormanager2.lib.hostconfig import read_host_config

logger = logging.getLogger(__name__)


class XMLRPCHandler(SimpleXMLRPCDispatcher):
    """
    Serve XML-RPC methods as a Flask view.

    This used to come from flask-xml-rpc, which is unmaintained upstream and has been
    retired from Fedora.  Only the handful of features MirrorManager uses are kept.
    """

    def __init__(self, endpoint_name):
        super().__init__(allow_none=True, encoding="utf-8")
        self.endpoint_name = endpoint_name
        self.register_introspection_functions()

    def register(self, function):
        """Register function as an XML-RPC method.  Can be used as a decorator."""
        return self.register_function(function)

    def connect(self, app, route):
        """Serve the registered methods at route on app."""
        app.add_url_rule(route, self.endpoint_name, self.handle_request, methods=["POST"])

    def handle_request(self):
        # _marshaled_dispatch() is private, but it is the only entry point the
        # dispatcher offers for an already read request body.
        response = self._marshaled_dispatch(request.data)
        return current_app.response_class(response, content_type="text/xml")


XMLRPC = XMLRPCHandler("xmlrpc")


@XMLRPC.register
def checkin(jsondata):
    uncompressed = bz2.decompress(base64.urlsafe_b64decode(jsondata))
    try:
        config = json.loads(uncompressed)
    except ValueError as e:
        logging.warning(f"Checkin is not JSON! ({e})")
        return "error checking in"
    r, host, message = read_host_config(DB.session, config)
    if r is not None:
        logging.info(f"Checkin for host {host} succesful: {message}")
        return message + "checked in successful"
    else:
        logging.error(f"Error for host {host} during checkin: {message}")
        return message + "error checking in"
