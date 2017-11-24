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
MirrorManager2 admin flask controller.
'''

import flask
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView

from mirrormanager2.app import APP, ADMIN, SESSION, is_mirrormanager_admin
from mirrormanager2.lib import model


class MMModelView(ModelView):
    ''' Base class for the Mirrormanager preventing access to the admin
    interface to non-admin.
    '''
    def is_accessible(self):
        ''' Prevent access to non-admin user. '''
        admin = False
        if hasattr(flask.g, 'fas_user') and flask.g.fas_user:
            admin = is_mirrormanager_admin(flask.g.fas_user)
        return admin


class DirectoryView(MMModelView):
    ''' View of the Host table specifying which field of the table should
    be shown (and their order).
    '''

    # Override displayed fields
    column_list = ('name', 'readable', 'ctime')


VIEWS = [
    MMModelView(model.Arch, SESSION),
    MMModelView(model.Category, SESSION),
    MMModelView(model.Country, SESSION, category='Country'),
    MMModelView(model.CountryContinentRedirect, SESSION, category='Country'),
    MMModelView(model.EmbargoedCountry, SESSION, category='Country'),
    DirectoryView(model.Directory, SESSION, category='Directory'),
    DirectoryView(model.DirectoryExclusiveHost, SESSION, category='Directory'),
    MMModelView(model.FileDetail, SESSION, category='File'),
    MMModelView(model.FileDetailFileGroup, SESSION, category='File'),
    MMModelView(model.FileGroup, SESSION, category='File'),
    MMModelView(model.Host, SESSION, category='Host'),
    MMModelView(model.HostAclIp, SESSION, category='Host'),
    MMModelView(model.HostCategory, SESSION, category='Host'),
    MMModelView(model.HostCategoryDir, SESSION, category='Host'),
    MMModelView(model.HostCategoryUrl, SESSION, category='Host'),
    MMModelView(model.HostCountry, SESSION, category='Host'),
    MMModelView(model.HostCountryAllowed, SESSION, category='Host'),
    MMModelView(model.HostLocation, SESSION, category='Host'),
    MMModelView(model.HostNetblock, SESSION, category='Host'),
    MMModelView(model.HostPeerAsn, SESSION, category='Host'),
    MMModelView(model.HostStats, SESSION, category='Host'),
    MMModelView(model.Location, SESSION),
    MMModelView(model.NetblockCountry, SESSION),
    MMModelView(model.Product, SESSION),
    MMModelView(model.Repository, SESSION, category='Repository'),
    MMModelView(model.RepositoryRedirect, SESSION, category='Repository'),
    MMModelView(model.Site, SESSION, category='Site'),
    MMModelView(model.SiteAdmin, SESSION, category='Site'),
    MMModelView(model.SiteToSite, SESSION, category='Site'),
    MMModelView(model.Version, SESSION),
]


if APP.config.get('MM_AUTHENTICATION', None) == 'local':
    VIEWS.append(MMModelView(model.User, SESSION))
    VIEWS.append(MMModelView(model.Group, SESSION))
    VIEWS.append(MMModelView(model.UserVisit, SESSION))


for view in VIEWS:
    ADMIN.add_view(view)
