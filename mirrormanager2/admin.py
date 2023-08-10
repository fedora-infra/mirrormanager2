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
MirrorManager2 admin flask controller.
"""

import flask
from flask_admin.contrib.sqla import ModelView

from mirrormanager2.lib import model
from mirrormanager2.perms import is_mirrormanager_admin


class MMModelView(ModelView):
    """Base class for the Mirrormanager preventing access to the admin
    interface to non-admin.
    """

    def is_accessible(self):
        """Prevent access to non-admin user."""
        admin = False
        if hasattr(flask.g, "fas_user") and flask.g.fas_user:
            admin = is_mirrormanager_admin(flask.g.fas_user)
        return admin


class DirectoryView(MMModelView):
    """View of the Host table specifying which field of the table should
    be shown (and their order).
    """

    # Override displayed fields
    column_list = ("name", "readable", "ctime")


def get_views(config, db_session):
    views = [
        MMModelView(model.Arch, db_session),
        MMModelView(model.Category, db_session),
        MMModelView(model.Country, db_session, category="Country"),
        MMModelView(model.CountryContinentRedirect, db_session, category="Country"),
        MMModelView(model.EmbargoedCountry, db_session, category="Country"),
        DirectoryView(model.Directory, db_session, category="Directory"),
        DirectoryView(model.DirectoryExclusiveHost, db_session, category="Directory"),
        MMModelView(model.FileDetail, db_session, category="File"),
        MMModelView(model.FileDetailFileGroup, db_session, category="File"),
        MMModelView(model.FileGroup, db_session, category="File"),
        MMModelView(model.Host, db_session, category="Host"),
        MMModelView(model.HostAclIp, db_session, category="Host"),
        MMModelView(model.HostCategory, db_session, category="Host"),
        MMModelView(model.HostCategoryDir, db_session, category="Host"),
        MMModelView(model.HostCategoryUrl, db_session, category="Host"),
        MMModelView(model.HostCountry, db_session, category="Host"),
        MMModelView(model.HostCountryAllowed, db_session, category="Host"),
        MMModelView(model.HostLocation, db_session, category="Host"),
        MMModelView(model.HostNetblock, db_session, category="Host"),
        MMModelView(model.HostPeerAsn, db_session, category="Host"),
        MMModelView(model.HostStats, db_session, category="Host"),
        MMModelView(model.Location, db_session),
        MMModelView(model.NetblockCountry, db_session),
        MMModelView(model.Product, db_session),
        MMModelView(model.Repository, db_session, category="Repository"),
        MMModelView(model.RepositoryRedirect, db_session, category="Repository"),
        MMModelView(model.Site, db_session, category="Site"),
        MMModelView(model.SiteAdmin, db_session, category="Site"),
        MMModelView(model.SiteToSite, db_session, category="Site"),
        MMModelView(model.Version, db_session),
    ]

    if config.get("MM_AUTHENTICATION", None) == "local":
        views.append(MMModelView(model.User, db_session))
        views.append(MMModelView(model.Group, db_session))
        views.append(MMModelView(model.UserVisit, db_session))

    return views


def register_views(app, admin, db_session):
    for view in get_views(app.config, db_session):
        admin.add_view(view)
