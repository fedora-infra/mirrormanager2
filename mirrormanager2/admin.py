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
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView

from mirrormanager2 import ADMIN, SESSION, is_mirrormanager_admin
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


class HostView(MMModelView):
    ''' View of the Host table specifying which field of the table should
    be shown (and their order).
    '''

    # Override displayed fields
    column_list = (
        'country', 'name', 'site_id', 'admin_active', 'user_active',
        'last_crawled', 'private', 'bandwidth_int', 'comment',
        'last_checked_in', 'internet2', 'internet2_client', 'asn',
        'asn_clients', 'max_connections', 'last_crawl_duration',
        'robot_email')


class DirectoryView(MMModelView):
    ''' View of the Host table specifying which field of the table should
    be shown (and their order).
    '''

    # Override displayed fields
    column_list = ('name', 'readable', 'ctime')


ADMIN.add_view(MMModelView(model.Arch, SESSION))
ADMIN.add_view(MMModelView(model.Category, SESSION))
ADMIN.add_view(MMModelView(model.Country, SESSION, category='Country'))
ADMIN.add_view(MMModelView(model.CountryContinentRedirect, SESSION, category='Country'))
ADMIN.add_view(MMModelView(model.EmbargoedCountry, SESSION, category='Country'))
ADMIN.add_view(DirectoryView(model.Directory, SESSION, category='Directory'))
ADMIN.add_view(DirectoryView(model.DirectoryExclusiveHost, SESSION, category='Directory'))
ADMIN.add_view(MMModelView(model.FileDetail, SESSION, category='File'))
ADMIN.add_view(MMModelView(model.FileDetailFileGroup, SESSION, category='File'))
ADMIN.add_view(MMModelView(model.FileGroup, SESSION, category='File'))
ADMIN.add_view(HostView(model.Host, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostAclIp, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostCategory, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostCategoryDir, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostCategoryUrl, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostCountry, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostCountryAllowed, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostLocation, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostNetblock, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostPeerAsn, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.HostStats, SESSION, category='Host'))
ADMIN.add_view(MMModelView(model.Location, SESSION))
ADMIN.add_view(MMModelView(model.NetblockCountry, SESSION))
ADMIN.add_view(MMModelView(model.Product, SESSION))
ADMIN.add_view(MMModelView(model.Repository, SESSION, category='Repository'))
ADMIN.add_view(MMModelView(model.RepositoryRedirect, SESSION, category='Repository'))
ADMIN.add_view(MMModelView(model.Site, SESSION, category='Site'))
ADMIN.add_view(MMModelView(model.SiteAdmin, SESSION, category='Site'))
ADMIN.add_view(MMModelView(model.SiteToSite, SESSION, category='Site'))
ADMIN.add_view(MMModelView(model.Version, SESSION))
