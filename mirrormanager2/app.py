# Copyright © 2014, 2015  Red Hat, Inc.
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
MirrorManager2 main flask controller.
"""


import logging
import logging.handlers
import os
import sys

import flask
from flask_admin import Admin
from sqlalchemy.orm import configure_mappers

from mirrormanager2 import __version__, local_auth
from mirrormanager2.admin import register_views as register_admin_views
from mirrormanager2.database import Database
from mirrormanager2.oidc import FedoraAuthCompat
from mirrormanager2.perms import is_mirrormanager_admin

OIDC = FedoraAuthCompat(prefix="oidc")
DB = Database()


def inject_variables():
    """Inject some variables into every template."""
    admin = False
    if hasattr(flask.g, "fas_user") and flask.g.fas_user:
        admin = is_mirrormanager_admin(flask.g.fas_user)
    return dict(is_admin=admin, version=__version__)


def create_app(config=None):
    app = flask.Flask(__name__)

    # Config
    app.config.from_object("mirrormanager2.default_config")
    if "MM2_CONFIG" in os.environ:  # pragma: no cover
        app.config.from_envvar("MM2_CONFIG")
    app.config.update(config or {})

    # Points the template and static folders to the desired theme
    app.template_folder = os.path.join(app.template_folder, app.config["THEME_FOLDER"])
    app.static_folder = os.path.join(app.static_folder, app.config["THEME_FOLDER"])

    # Set up the logger
    # Send emails for big exception
    MAIL_HANDLER = logging.handlers.SMTPHandler(
        app.config.get("SMTP_SERVER", "127.0.0.1"),
        "nobody@fedoraproject.org",
        app.config.get("MAIL_ADMIN", "admin@fedoraproject.org"),
        "MirrorManager2 error",
    )
    MAIL_HANDLER.setFormatter(
        logging.Formatter(
            """
        Message type:       %(levelname)s
        Location:           %(pathname)s:%(lineno)d
        Module:             %(module)s
        Function:           %(funcName)s
        Time:               %(asctime)s

        Message:

        %(message)s
    """
        )
    )
    MAIL_HANDLER.setLevel(logging.ERROR)
    if not app.debug:
        app.logger.addHandler(MAIL_HANDLER)

    # Log to stderr as well
    STDERR_LOG = logging.StreamHandler(sys.stderr)
    STDERR_LOG.setLevel(logging.INFO)
    app.logger.addHandler(STDERR_LOG)

    # Database
    DB.init_app(app)

    # Auth
    if app.config.get("MM_AUTHENTICATION") == "fas":
        OIDC.init_app(app)
    elif app.config.get("MM_AUTHENTICATION") == "local":
        app.register_blueprint(local_auth.views, prefix="auth")

    # Admin UI
    # Flask-Admin does not support having a single instance and multiple calls
    # to init_app() (it stores the app as an instance attribute)
    ADMIN = Admin(template_mode="bootstrap3")
    # Force mapper configuration here because flask-admin does relationship
    # introspection that will fail to recognize relationships if they haven't
    # been configured (and if no query has been emitted yet).
    configure_mappers()
    # Now init Flask-Admin
    ADMIN.init_app(app)
    register_admin_views(app, ADMIN, DB.session)

    # Template variables
    app.context_processor(inject_variables)

    # Views
    from mirrormanager2.auth import views as auth_views

    app.register_blueprint(auth_views)
    from mirrormanager2.views import views as base_views

    app.register_blueprint(base_views)
    from mirrormanager2.api import views as api_views

    app.register_blueprint(api_views, prefix="api")
    from mirrormanager2.xml_rpc import XMLRPC

    XMLRPC.connect(app, "/xmlrpc")

    return app
