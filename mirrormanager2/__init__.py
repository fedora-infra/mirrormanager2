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
MirrorManager2 main flask controller.
'''


import logging
import logging.handlers
import os
import sys

import flask

from functools import wraps

__version__ = '2.0.1'

APP = flask.Flask(__name__)

APP.config.from_object('mirrormanager2.default_config')
if 'MM2_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('MM2_CONFIG')


if APP.config.get('MM_AUTHENTICATION') == 'FAS':
    # Use FAS for authentication
    from flask.ext.fas_openid import FAS
    FAS = FAS(APP)


# Points the template and static folders to the desired theme
APP.template_folder = os.path.join(
    APP.template_folder, APP.config['THEME_FOLDER'])
APP.static_folder = os.path.join(
    APP.static_folder, APP.config['THEME_FOLDER'])


# Set up the logger
## Send emails for big exception
MAIL_HANDLER = logging.handlers.SMTPHandler(
    APP.config.get('SMTP_SERVER', '127.0.0.1'),
    'nobody@fedoraproject.org',
    APP.config.get('MAIL_ADMIN', 'admin@fedoraproject.org'),
    'MirrorManager2 error')
MAIL_HANDLER.setFormatter(logging.Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
'''))
MAIL_HANDLER.setLevel(logging.ERROR)
if not APP.debug:
    APP.logger.addHandler(MAIL_HANDLER)

# Log to stderr as well
STDERR_LOG = logging.StreamHandler(sys.stderr)
STDERR_LOG.setLevel(logging.INFO)
APP.logger.addHandler(STDERR_LOG)

LOG = APP.logger


import mirrormanager2.lib as mmlib


SESSION = mmlib.create_session(APP.config['DB_URL'])


def is_mirrormanager_admin(user):
    """ Is the user a mirrormanager admin.
    """
    if not user:
        return False
    if APP.config.get('MM_AUTHENTICATION', None) == 'FAS':
        if not user.cla_done or len(user.groups) < 1:
            return False

        admins = APP.config['ADMIN_GROUP']
        if isinstance(admins, basestring):
            admins = [admins]
        admins = set(admins)

        return len(admins.intersection(set(user.groups))) > 0
    else:
        return user in APP.config['ADMIN_GROUP']


## Flask application
@APP.route('/')
def index():
    """ Displays the index page.
    """
    return flask.render_template(
        'index.html',
    )
