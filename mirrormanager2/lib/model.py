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
MirrorManager2 database model.
'''

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import datetime
import logging
import time

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relation
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.collections import mapped_collection
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_
from sqlalchemy.sql.expression import Executable, ClauseElement

BASE = declarative_base()

ERROR_LOG = logging.getLogger('mirrormanager2.lib.model')

## Apparently some of our methods have too few public methods
# pylint: disable=R0903
## Others have too many attributes
# pylint: disable=R0902
## Others have too many arguments
# pylint: disable=R0913
## We use id for the identifier in our db but that's too short
# pylint: disable=C0103
## Some of the object we use here have inherited methods which apparently
## pylint does not detect.
# pylint: disable=E1101


def create_tables(db_url, alembic_ini=None, debug=False):
    """ Create the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary
        to be able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.

    """
    engine = create_engine(db_url, echo=debug)
    BASE.metadata.create_all(engine)
    if db_url.startswith('sqlite:'):
        ## Ignore the warning about con_record
        # pylint: disable=W0613
        def _fk_pragma_on_connect(dbapi_con, con_record):
            ''' Tries to enforce referential constraints on sqlite. '''
            dbapi_con.execute('pragma foreign_keys=ON')
        sa.event.listen(engine, 'connect', _fk_pragma_on_connect)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:

        ## Ignore the warning missing alembic
        # pylint: disable=F0401
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def drop_tables(db_url, engine):  # pragma: no cover
    """ Drops the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    """
    engine = create_engine(db_url)
    BASE.metadata.drop_all(engine)


class Site(BASE):

    __tablename__ = 'site'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False)
    password = sa.Column(sa.Text(), default=None, nullable=True)
    org_url = sa.Column(sa.Text(), default=None, nullable=True)
    private = sa.Column(sa.Boolean(), default=False, nullable=False)
    admin_active = sa.Column(sa.Boolean(), default=True, nullable=False)
    user_active = sa.Column(sa.Boolean(), default=True, nullable=False)
    created_at = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    created_by = sa.Column(sa.Text(), nullable=False)
    # allow all sites to pull from me
    all_sites_can_pull_from_me = sa.Column(
        sa.Boolean(), default=False, nullable=False)
    downstream_comments = sa.Column(sa.Text(), default=None, nullable=True)
    email_on_drop = sa.Column(sa.Boolean(), default=False, nullable=False)
    email_on_add = sa.Column(sa.Boolean(), default=False, nullable=False)

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return '<Site(%s - %s)>' % (self.id, self.name)

class Country(BASE):

    __tablename__ = 'country'

    id = sa.Column(sa.Integer, primary_key=True)
    code = sa.Column(sa.Text(), nullable=False, unique=True)
    #hosts = SQLRelatedJoin('Host')


class Host(BASE):

    __tablename__ = 'host'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False)
    site_id = sa.Column(
        sa.Integer, sa.ForeignKey('site.id'), nullable=True)
    robot_email = sa.Column(sa.Text(), nullable=True)
    admin_active = sa.Column(sa.Boolean(), default=True, nullable=False)
    user_active = sa.Column(sa.Boolean(), default=True, nullable=False)
    country = sa.Column(sa.Text(), nullable=False)
    bandwidth_int = sa.Column(sa.Integer, default=100, nullable=True)
    comment = sa.Column(sa.Text(), nullable=True)
    #_config = PickleCol(default=None)
    last_checked_in = sa.Column(sa.DateTime, nullable=True, default=None)
    last_crawled = sa.Column(sa.DateTime, nullable=True, default=None)
    private = sa.Column(sa.Boolean(), default=False, nullable=False)
    internet2 = sa.Column(sa.Boolean(), default=False, nullable=False)
    internet2_clients = sa.Column(sa.Boolean(), default=False, nullable=False)
    asn = sa.Column(sa.Integer, default=None, nullable=True)
    asn_clients = sa.Column(sa.Boolean(), default=True, nullable=False)
    max_connections = sa.Column(sa.Integer, default=1, nullable=False)
    last_crawl_duration = sa.Column(sa.BigInteger, default=0, nullable=True)

    # Relations
    site = relation(
        'Site',
        foreign_keys=[site_id], remote_side=[Site.id],
        backref=backref('hosts')
    )

    #exclusive_dirs = MultipleJoin('DirectoryExclusiveHost')
    #locations = SQLRelatedJoin('Location')
    #countries = SQLRelatedJoin('Country')

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'site_id', 'name', name='host_idx'),
    )

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return '<Host(%s - %s)>' % (self.id, self.name)


class Directory(BASE):

    __tablename__ = 'directory'

    id = sa.Column(sa.Integer, primary_key=True)
    # Full path
    # e.g. pub/epel
    # e.g. pub/fedora/linux
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    files = sa.Column(sa.LargeBinary(), nullable=True)
    readable = sa.Column(sa.Boolean(), default=True, nullable=False)
    ctime = sa.Column(sa.BigInteger, default=0, nullable=True)

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return '<Directory(%s - %s)>' % (self.id, self.name)

# e.g. 'fedora' and 'epel'
class Product(BASE):

    __tablename__ = 'product'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    publiclist = sa.Column(sa.Boolean(), default=True, nullable=False)

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return '<Product(%s - %s)>' % (self.id, self.name)

class Category(BASE):

    __tablename__ = 'category'

    id = sa.Column(sa.Integer, primary_key=True)
    # Top-level mirroring
    # e.g. 'Fedora Linux', 'Fedora Archive'
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    canonicalhost = sa.Column(
        sa.Text(), nullable=True,
        default='http://download.fedora.redhat.com')
    publiclist = sa.Column(sa.Boolean(), default=True, nullable=False)
    geo_dns_domain = sa.Column(sa.Text(), nullable=True)
    product_id = sa.Column(
        sa.Integer, sa.ForeignKey('product.id'), nullable=True)
    topdir_id = sa.Column(
        sa.Integer, sa.ForeignKey('directory.id'), nullable=True)

    # Relations
    product = relation(
        'Product',
        foreign_keys=[product_id], remote_side=[Product.id],
        backref=backref('categories')
    )
    topdir = relation(
        'Directory',
        foreign_keys=[topdir_id], remote_side=[Directory.id],
    )

    # all the directories that are part of this category
    #directories = RelatedJoin('Directory', orderBy='name')

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return '<Category(%s - %s)>' % (self.id, self.name)

class SiteToSite(BASE):

    __tablename__ = 'site_to_site'

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.Text(), default=None, nullable=True)
    password = sa.Column(sa.Text(), default=None, nullable=True)
    upstream_site_id = sa.Column(
        sa.Integer, sa.ForeignKey('site.id'), nullable=False)
    downstream_site_id = sa.Column(
        sa.Integer, sa.ForeignKey('site.id'), nullable=False)

    # Relations
    upstream_site = relation(
        'Site',
        foreign_keys=[upstream_site_id], remote_side=[Site.id],
    )
    downstream_site = relation(
        'Site',
        foreign_keys=[downstream_site_id], remote_side=[Site.id],
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'upstream_site_id', 'downstream_site_id',
            name='site_to_site_idx'),
        sa.UniqueConstraint(
            'upstream_site_id', 'username',
            name='site_to_site_username_idx'),
    )


class SiteAdmin(BASE):

    __tablename__ = 'site_admin'

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.Text(), default=None, nullable=True)
    site_id = sa.Column(
        sa.Integer, sa.ForeignKey('site.id'), nullable=False)

    # Relation
    site = relation(
        'Site',
        foreign_keys=[site_id], remote_side=[Site.id],
        backref=backref('admins'),
    )


class HostCategory(BASE):

    __tablename__ = 'host_category'

    id = sa.Column(sa.Integer, primary_key=True)
    host_id = sa.Column(sa.Integer, sa.ForeignKey('host.id'), nullable=True)
    category_id = sa.Column(
        sa.Integer, sa.ForeignKey('category.id'), nullable=True)
    always_up2date = sa.Column(sa.Boolean(), default=False, nullable=False)

    # Relations
    category = relation(
        'Category',
        foreign_keys=[category_id], remote_side=[Category.id],
        backref=backref('host_categories')
    )

    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
        backref=backref('categories')
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'host_id', 'category_id', name='host_category_hcindex'),
    )

    def my_site(self):
        return self.host.my_site()

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return '<HostCategory(%s - %s)>' % (self.id, self.category)


class HostCategoryDir(BASE):

    __tablename__ = 'host_category_dir'

    id = sa.Column(sa.Integer, primary_key=True)
    host_category_id = sa.Column(
        sa.Integer, sa.ForeignKey('host_category.id'), nullable=True)
    # subset of the path starting below HostCategory.path
    path = sa.Column(sa.Text(), nullable=True)
    up2date = sa.Column(
        sa.Boolean, default=True, nullable=False, index=True)
    directory_id = sa.Column(
        sa.Integer, sa.ForeignKey('directory.id'), nullable=True)

    # Relations
    directory = relation(
        'Directory',
        foreign_keys=[directory_id], remote_side=[Directory.id],
        backref=backref('host_category_dirs'),
    )

    host_category = relation(
        'HostCategory',
        foreign_keys=[host_category_id], remote_side=[HostCategory.id],
        backref=backref('dirs', order_by=path),
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'host_category_id', 'path', name='host_category_dir_hcdindex'),
    )


class HostCategoryUrl(BASE):

    __tablename__ = 'host_category_url'

    id = sa.Column(sa.Integer, primary_key=True)
    host_category_id = sa.Column(
        sa.Integer, sa.ForeignKey('host_category.id'), nullable=True)
    url = sa.Column(sa.Text(), nullable=False, unique=True)
    private = sa.Column(sa.Boolean(), default=False, nullable=False)

    # Relations
    host_category = relation(
        'HostCategory',
        foreign_keys=[host_category_id], remote_side=[HostCategory.id],
        backref=backref('urls'),
    )

    def my_site(self):
        return self.host_category.my_site()


class HostAclIp(BASE):

    __tablename__ = 'host_acl_ip'

    id = sa.Column(sa.Integer, primary_key=True)
    ip = sa.Column(sa.Text(), nullable=True, unique=True)
    host_id = sa.Column(
        sa.Integer, sa.ForeignKey('host.id'), nullable=True)

    # Relation
    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
        backref=backref('acl_ips', order_by='HostAclIp.ip'),
    )

    def my_site(self):
        return self.host.my_site()


class HostCountryAllowed(BASE):

    __tablename__ = 'host_country_allowed'

    id = sa.Column(sa.Integer, primary_key=True)
    country = sa.Column(sa.Text(), nullable=False, unique=True)
    host_id = sa.Column(
        sa.Integer, sa.ForeignKey('host.id'), nullable=True)

    # Relation
    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
        backref=backref('countries_allowed'),
    )

    def my_site(self):
        return self.host.my_site()


class HostNetblock(BASE):

    __tablename__ = 'host_netblock'

    id = sa.Column(sa.Integer, primary_key=True)
    netblock = sa.Column(sa.Text(), nullable=True)
    name = sa.Column(sa.Text(), nullable=True)
    host_id = sa.Column(
        sa.Integer, sa.ForeignKey('host.id'), nullable=True)

    # Relation
    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
        backref=backref('netblocks', order_by='HostNetblock.netblock'),
    )

    def my_site(self):
        return self.host.my_site()


class HostPeerAsn(BASE):

    __tablename__ = 'host_peer_asn'

    id = sa.Column(sa.Integer, primary_key=True)
    asn = sa.Column(sa.Integer, nullable=False)
    name = sa.Column(sa.Text(), nullable=True)
    host_id = sa.Column(
        sa.Integer, sa.ForeignKey('host.id'), nullable=True)

    # Relation
    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
        backref=backref('peer_asns'),
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'host_id', 'asn', name='host_peer_asn_idx'),
    )


class HostStats(BASE):

    __tablename__ = 'host_stats'

    id = sa.Column(sa.Integer, primary_key=True)
    timestamp = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    type = sa.Column(sa.Text(), nullable=True)
    data = sa.Column(sa.LargeBinary(), nullable=True)
    host_id = sa.Column(
        sa.Integer, sa.ForeignKey('host.id'), nullable=True)

    # Relation
    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
    )


class Arch(BASE):

    __tablename__ = 'arch'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    publiclist = sa.Column(sa.Boolean(), default=True, nullable=False)
    primary_arch = sa.Column(sa.Boolean(), default=True, nullable=False)

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return '<Arch(%s - %s)>' % (self.id, self.name)

class Version(BASE):

    __tablename__ = 'version'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=True)
    codename = sa.Column(sa.Text(), nullable=True)
    is_test = sa.Column(sa.Boolean(), default=False, nullable=False)
    display = sa.Column(sa.Boolean(), default=True, nullable=False)
    display_name = sa.Column(sa.Text(), nullable=True)
    ordered_mirrorlist = sa.Column(sa.Boolean(), default=True, nullable=False)
    sortorder = sa.Column(sa.Integer, default=0, nullable=False)
    product_id = sa.Column(
        sa.Integer, sa.ForeignKey('product.id'), nullable=True)

    # Relations
    product = relation(
        'Product',
        foreign_keys=[product_id], remote_side=[Product.id],
        backref=backref('versions'),
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'name', 'product_id', name='version_idx'),
    )

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return '<Version(%s - %s)>' % (self.id, self.name)


class Repository(BASE):

    __tablename__ = 'repository'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    prefix = sa.Column(sa.Text(), nullable=True)
    category_id = sa.Column(
        sa.Integer, sa.ForeignKey('category.id'), nullable=True)
    version_id = sa.Column(
        sa.Integer, sa.ForeignKey('version.id'), nullable=True)
    arch_id = sa.Column(
        sa.Integer, sa.ForeignKey('arch.id'), nullable=True)
    directory_id = sa.Column(
        sa.Integer, sa.ForeignKey('directory.id'), nullable=True)
    disabled = sa.Column(sa.Boolean(), default=False, nullable=False)

    # Relations
    category = relation(
        'Category',
        foreign_keys=[category_id], remote_side=[Category.id],
        backref=backref('repositories')
    )
    version = relation(
        'Version',
        foreign_keys=[version_id], remote_side=[Version.id],
    )
    arch = relation(
        'Arch',
        foreign_keys=[arch_id], remote_side=[Arch.id],
    )
    directory = relation(
        'Directory',
        foreign_keys=[directory_id], remote_side=[Directory.id],
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'prefix', 'arch_id', name='repository_idx'),
    )


class FileDetail(BASE):

    __tablename__ = 'file_detail'

    id = sa.Column(sa.Integer, primary_key=True)
    filename = sa.Column(sa.Text(), nullable=False)
    timestamp = sa.Column(sa.BigInteger, default=None, nullable=True)
    size = sa.Column(sa.BigInteger, default=None, nullable=True)
    sha1 = sa.Column(sa.Text(), nullable=True)
    md5 = sa.Column(sa.Text(), nullable=True)
    sha256 = sa.Column(sa.Text(), nullable=True)
    sha512 = sa.Column(sa.Text(), nullable=True)
    directory_id = sa.Column(
        sa.Integer, sa.ForeignKey('directory.id'), nullable=False)

    # Relations
    directory = relation(
        'Directory',
        foreign_keys=[directory_id], remote_side=[Directory.id],
    )

    #fileGroups = SQLRelatedJoin('FileGroup')


class RepositoryRedirect(BASE):

    __tablename__ = 'repository_redirect'

    # Uses strings to allow for effective named aliases, and for repos
    # that may not exist yet
    id = sa.Column(sa.Integer, primary_key=True)
    to_repo = sa.Column(sa.Text(), nullable=True)
    from_repo = sa.Column(sa.Text(), nullable=False, unique=True)

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'from_repo', 'to_repo', name='repository_redirect_idx'),
    )


class CountryContinentRedirect(BASE):

    __tablename__ = 'country_continent_redirect'

    id = sa.Column(sa.Integer, primary_key=True)
    country = sa.Column(sa.Text(), nullable=False, unique=True)
    continent = sa.Column(sa.Text(), nullable=False)


class EmbargoedCountry(BASE):

    __tablename__ = 'embargoed_country'

    id = sa.Column(sa.Integer, primary_key=True)
    country_code = sa.Column(sa.Text(), nullable=False, unique=True)


class DirectoryExclusiveHost(BASE):

    __tablename__ = 'directory_exclusive_host'

    id = sa.Column(sa.Integer, primary_key=True)
    directory_id = sa.Column(
        sa.Integer, sa.ForeignKey('directory.id'), nullable=False)
    host_id = sa.Column(
        sa.Integer, sa.ForeignKey('host.id'), nullable=False)

    # Relations
    directory = relation(
        'Directory',
        foreign_keys=[directory_id], remote_side=[Directory.id],
    )
    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'directory_id', 'host_id', name='directory_exclusive_host_idx'),
    )


class Location(BASE):
    """For grouping hosts, perhaps across Site boundaries.  User queries
    may request hosts from a particular Location (such as an Amazon region),
    which will be returned first in the mirror list. """

    __tablename__ = 'location'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)

    #hosts = SQLRelatedJoin('Host')


# manual creation of the RelatedJoin table so we can guarantee uniqueness
class HostLocation(BASE):

    __tablename__ = 'host_location'

    id = sa.Column(sa.Integer, primary_key=True)
    location_id = sa.Column(
        sa.Integer, sa.ForeignKey('location.id'), nullable=False)
    host_id = sa.Column(
        sa.Integer, sa.ForeignKey('host.id'), nullable=False)

    # Relations
    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
        #backref=backref('hosts')
    )
    location = relation(
        'Location',
        foreign_keys=[location_id], remote_side=[Location.id],
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'location_id', 'host_id', name='host_location_hlidx'),
    )


class FileGroup(BASE):

    __tablename__ = 'file_group'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)

    #files = SQLRelatedJoin('FileDetail')


class FileDetailFileGroup(BASE):

    __tablename__ = 'file_detail_file_group'

    id = sa.Column(sa.Integer, primary_key=True)
    file_detail_id = sa.Column(
        sa.Integer, sa.ForeignKey('file_detail.id'), nullable=False)
    file_group_id = sa.Column(
        sa.Integer, sa.ForeignKey('file_group.id'), nullable=False)

    # Relations
    file_detail = relation(
        'FileDetail',
        foreign_keys=[file_detail_id], remote_side=[FileDetail.id],
        #backref=backref('hosts')
    )
    file_group = relation(
        'FileGroup',
        foreign_keys=[file_group_id], remote_side=[FileGroup.id],
    )


class HostCountry(BASE):

    __tablename__ = 'host_country'

    id = sa.Column(sa.Integer, primary_key=True)
    country_id = sa.Column(
        sa.Integer, sa.ForeignKey('country.id'), nullable=False)
    host_id = sa.Column(
        sa.Integer, sa.ForeignKey('host.id'), nullable=False)
    country_id = sa.Column(
        sa.Integer, sa.ForeignKey('country.id'), nullable=False)

    # Relations
    host = relation(
        'Host',
        foreign_keys=[host_id], remote_side=[Host.id],
        #backref=backref('hosts')
    )
    country = relation(
        'Country',
        foreign_keys=[country_id], remote_side=[Country.id],
        #backref=backref('hosts')
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'host_id', 'country_id', name='host_country_hlidx'),
    )


class NetblockCountry(BASE):

    __tablename__ = 'netblock_country'

    id = sa.Column(sa.Integer, primary_key=True)
    netblock = sa.Column(sa.Text(), nullable=False, unique=True)
    country = sa.Column(sa.Text(), nullable=False)


###############################################################
# These classes are only used if you're not using the
# Fedora Account System or some other backend that provides
# Identity management
class Visit(BASE):

    __tablename__ = 'visit'

    id = sa.Column(sa.Integer, primary_key=True)
    visit_key = sa.Column(sa.String(40), nullable=False, unique=True)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    expiry = sa.Column(sa.DateTime)


class VisitIdentity(BASE):

    __tablename__ = 'visit_identity'

    id = sa.Column(sa.Integer, primary_key=True)
    visit_key = sa.Column(sa.String(40), nullable=False, unique=True)
    user_id = sa.Column(
        sa.Integer, sa.ForeignKey('mm_user.id'), nullable=False)


class Group(BASE):
    """
    An ultra-simple group definition.
    """

    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    __tablename__ = 'mm_group'

    id = sa.Column(sa.Integer, primary_key=True)
    group_name = sa.Column(sa.String(16), nullable=False, unique=True)
    display_name = sa.Column(sa.String(255), nullable=True)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow)

    ## collection of all users belonging to this group
    #users = RelatedJoin("User", intermediateTable="user_group",
                        #joinColumn="group_id", otherColumn="user_id")

    ## collection of all permissions for this group
    #permissions = RelatedJoin("Permission", joinColumn="group_id",
                              #intermediateTable="group_permission",
                              #otherColumn="permission_id")


class UserGroup(BASE):

    __tablename__ = 'user_group'

    user_id = sa.Column(
        sa.Integer, sa.ForeignKey('mm_user.id'), primary_key=True)
    group_id = sa.Column(
        sa.Integer, sa.ForeignKey('mm_group.id'), primary_key=True)

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'user_id', 'group_id'),
    )


class User(BASE):
    """
    Reasonably basic User definition. Probably would want additional
    attributes.
    """
    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    __tablename__ = 'mm_user'

    id = sa.Column(sa.Integer, primary_key=True)
    user_name = sa.Column(sa.String(16), nullable=False, unique=True)
    email_address = sa.Column(sa.String(255), nullable=False, unique=True)
    display_name = sa.Column(sa.String(255), nullable=True)
    password = sa.Column(sa.String(40), nullable=True)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow)

    # groups this user belongs to
    #groups = RelatedJoin("Group", intermediateTable="user_group",
                         #joinColumn="user_id", otherColumn="group_id")


class Permission(BASE):

    __tablename__ = 'permission'

    id = sa.Column(sa.Integer, primary_key=True)

    permission_name = sa.Column(sa.String(16), nullable=False, unique=True)
    description = sa.Column(sa.String(255), nullable=True)

    #groups = RelatedJoin("Group",
                        #intermediateTable="group_permission",
                         #joinColumn="permission_id",
                         #otherColumn="group_id")


class GroupPermission(BASE):

    __tablename__ = 'group_permission'

    permission_id = sa.Column(
        sa.Integer, sa.ForeignKey('permission.id'), primary_key=True)
    group_id = sa.Column(
        sa.Integer, sa.ForeignKey('mm_group.id'), primary_key=True)

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'permission_id', 'group_id'),
    )
