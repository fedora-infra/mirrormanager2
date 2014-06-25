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
import random
import string

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


def get_siteadmin(session, admin_id):
    ''' Return a specified SiteAdmin via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.SiteAdmin
    ).filter(
        model.SiteAdmin.id == admin_id
    )

    return query.first()


def get_all_sites(session):
    ''' Return all existing Site.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Site
    ).order_by(
        model.Site.name, model.Site.created_at
    )

    return query.all()


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


def get_host_category(session, host_category_id):
    ''' Return a specified HostCategory via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategory
    ).filter(
        model.HostCategory.id == host_category_id
    )

    return query.first()


def get_host_category_by_hostid_category(session, host_id, category):
    ''' Return all HostCategory having the specified host_id and category.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategory
    ).filter(
        model.HostCategory.host_id == host_id
    ).filter(
        model.HostCategory.category_id == Category.id
    ).filter(
        model.Category.name == category
    )

    return query.all()


def get_host_category_url(session, host_category_url_id):
    ''' Return a specified HostCategoryUrl via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategoryUrl
    ).filter(
        model.HostCategoryUrl.id == host_category_url_id
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


def get_user_by_username(session, username):
    ''' Return a specified User via its username.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.User
    ).filter(
        model.User.user_name == username
    )

    return query.first()


def get_user_by_email(session, email):
    ''' Return a specified User via its email address.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.User
    ).filter(
        model.User.email_address == email
    )

    return query.first()


def get_user_by_token(session, token):
    ''' Return a specified User via its token.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.User
    ).filter(
        model.User.token == token
    )

    return query.first()


def get_session_by_visitkey(session, sessionid):
    ''' Return a specified VisitUser via its session identifier (visit_key).

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.UserVisit
    ).filter(
        model.UserVisit.visit_key == sessionid
    )

    return query.first()


def get_version_by_name_version(session, p_name, p_version):
    ''' Return a specified Version given the Product name and Version name
    provided.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Version
    ).filter(
        model.Version.product_id == model.Product.id
    ).filter(
        model.Product.name == p_name
    ).filter(
        model.Version.name == p_version
    )

    return query.first()


def get_versions(session):
    ''' Return the list of all versions in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Version
    ).order_by(
        model.Version.id
    )

    return query.all()


def get_arch_by_name(session, arch_name):
    ''' Return a Arch specified via name.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Arch
    ).filter(
        model.Arch.name == arch_name
    )

    return query.first()


def get_categories(session):
    ''' Return the list of all the categories in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Category
    )

    return query.all()


def get_products(session):
    ''' Return the list of all the products in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Product
    ).order_by(
        model.Product.name
    )

    return query.all()


def get_arches(session):
    ''' Return the list of all the arch in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Arch
    ).order_by(
        model.Arch.name
    )

    return query.all()


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
        up2date=None, host_category_url_private=None,
        version_id=None, arch_id=None):
    ''' Retrieve the mirrors based on the criteria specified.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        sqlalchemy.func.distinct(model.Host.id)
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

    if version_id is not None:
        query = query.filter(
            model.Host.id == model.HostCategory.host_id
        ).filter(
            model.HostCategory.category_id == model.Category.id
        ).filter(
            model.Category.id == model.Repository.category_id
        ).filter(
            model.Repository.version_id == version_id
        )

    if arch_id is not None:
        query = query.filter(
            model.Host.id == model.HostCategory.host_id
        ).filter(
            model.HostCategory.category_id == model.Category.id
        ).filter(
            model.Category.id == model.Repository.category_id
        ).filter(
            model.Repository.arch_id == arch_id
        )

    final_query = session.query(
        model.Host
    ).filter(
        model.Host.id.in_(query.subquery())
    ).order_by(
        model.Host.country, model.Host.name
    )

    return final_query.all()


def get_user_sites(session, username):
    """ Return the list of sites the specified user is admin of.
    """
    query = session.query(
        model.Site
    ).filter(
        model.Site.id == model.SiteAdmin.site_id
    ).filter(
        model.SiteAdmin.username == username
    ).order_by(
        model.Site.name, model.Site.created_at
    )

    return query.all()


def id_generator(size=15, chars=string.ascii_uppercase + string.digits):
    """ Generates a random identifier for the given size and using the
    specified characters.
    If no size is specified, it uses 15 as default.
    If no characters are specified, it uses ascii char upper case and
    digits.
    :arg size: the size of the identifier to return.
    :arg chars: the list of characters that can be used in the
        idenfitier.
    """
    return ''.join(random.choice(chars) for x in range(size))


def get_directory_by_name(session, dirname):
    ''' Return a specified Directory via its name.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Directory
    ).filter(
        model.Directory.name == dirname
    )

    return query.first()


def get_hostcategorydir_by_hostcategoryid_and_path(
        session, host_category_id, path):
    ''' Return all HostCategoryDir via its host_category_id and path.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategoryDir
    ).filter(
        model.HostCategoryDir.path == path
    ).filter(
        model.HostCategoryDir.host_category_id == host_category_id
    )

    return query.all()
