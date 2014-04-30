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
MirrorManager2 internal api.
'''

import datetime

import sqlalchemy

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

from mirrormanager2.lib import model


def create_session(db_url, debug=False, pool_recycle=3600):
    ''' Create the Session object to use to query the database.

    :arg db_url: URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg debug: a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a Session that can be used to query the database.

    '''
    engine = sqlalchemy.create_engine(
        db_url, echo=debug, pool_recycle=pool_recycle)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def get_site(session, site_id):
    ''' Return a specified Site via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Site
    ).filter(
        model.Site.id == site_id
    )

    return query.first()


def get_host(session, host_id):
    ''' Return a specified Host via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Host
    ).filter(
        model.Host.id == host_id
    )

    return query.first()


def get_host_acl_ip(session, host_acl_ip_id):
    ''' Return a specified HostAclIp via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostAclIp
    ).filter(
        model.HostAclIp.id == host_acl_ip_id
    )

    return query.first()


def get_host_netblock(session, host_netblock_id):
    ''' Return a specified HostNetblock via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostNetblock
    ).filter(
        model.HostNetblock.id == host_netblock_id
    )

    return query.first()


def get_host_peer_asn(session, host_asn_id):
    ''' Return a specified HostPeerAsn via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostPeerAsn
    ).filter(
        model.HostPeerAsn.id == host_asn_id
    )

    return query.first()


def get_host_country(session, host_country_id):
    ''' Return a specified HostCountry via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCountry
    ).filter(
        model.HostCountry.id == host_country_id
    )

    return query.first()


def get_country_by_name(session, country_code):
    ''' Return a specified Country via its two letter code.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Country
    ).filter(
        model.Country.code == country_code
    )

    return query.first()


def add_admin_to_site(session, site, admin):
    ''' Add an admin to the specified site.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.SiteAdmin
    ).filter(
        model.SiteAdmin.site_id == site_id
    )

    admins = [sa.username for sa in query.all()]

    if admin in admins:
        return '%s was already listed as an admin' % admin
    else:
        sa = model.SiteAdmin(site_id=site_id, username=admin)
        session.add(sa)
        session.flush()
        return '%s added as an admin' % admin


def get_mirrors(
        session, private=None, internet2=None, internet2_clients=None,
        asn_clients=None, admin_active=None, user_active=None, urls=None,
        last_crawl_duration=False, last_checked_in=False, last_crawled=False,
        site_private=None, site_admin_active=None, site_user_active=None,
        up2date=None, host_category_url_private=None):
    ''' Retrieve the mirrors based on the criteria specified.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Host
    ).order_by(
        model.Host.country, model.Host.name
    )

    if private is not None:
        query = query.filter(model.Host.private == private)
    if internet2 is not None:
        query = query.filter(model.Host.internet2 == internet2)
    if internet2_clients is not None:
        query = query.filter(model.Host.internet2_clients == internet2_clients)
    if asn_clients is not None:
        query = query.filter(model.Host.asn_clients == asn_clients)
    if admin_active is not None:
        query = query.filter(model.Host.admin_active == admin_active)
    if user_active is not None:
        query = query.filter(model.Host.user_active == user_active)

    if host_category_url_private is not None:
        query = query.filter(
            model.HostCategory.host_id == model.Host.id
        ).filter(
            model.HostCategoryUrl.host_category_id == model.HostCategory.id
        ).filter(
            model.HostCategoryUrl.private == host_category_url_private
        )

    if last_crawl_duration is True:
        query = query.filter(model.Host.last_crawl_duration > 0)
    if last_crawled is True:
        query = query.filter(model.Host.last_crawled != None)
    if last_checked_in is True:
        query = query.filter(model.Host.last_checked_in != None)

    if site_private is not None:
        query = query.filter(
            model.Host.site_id == model.Site.id
        ).filter(
            model.Site.private == site_private
        )
    if site_user_active is not None:
        query = query.filter(
            model.Host.site_id == model.Site.id
        ).filter(
            model.Site.user_active == site_user_active
        )
    if site_admin_active is not None:
        query = query.filter(
            model.Host.site_id == model.Site.id
        ).filter(
            model.Site.admin_active == site_admin_active
        )

    if up2date is not None:
        query = query.filter(
            model.Host.id == model.HostCategory.host_id
        ).filter(
            model.HostCategory.id == model.HostCategoryDir.host_category_id
        ).filter(
            model.HostCategoryDir.up2date == up2date
        )

    return query.all()
