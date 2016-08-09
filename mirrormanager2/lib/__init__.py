# -*- coding: utf-8 -*-
#
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


def get_site_by_name(session, site_name):
    ''' Return a specified Site via its name.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Site
    ).filter(
        model.Site.name == site_name
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


def get_siteadmins(session):
    ''' Return all SiteAdmin present in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.SiteAdmin
    ).order_by(
        model.SiteAdmin.username
    )

    return query.all()


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


def get_host_by_name(session, host_name):
    ''' Return a specified Host via its name.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Host
    ).filter(
        model.Host.name == host_name
    )

    return query.first()


def get_hosts(session):
    ''' Return all Hosts in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Host
    ).order_by(
        model.Host.id
    )

    return query.all()


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


def get_host_category_dirs(session):
    ''' Return all the HostCategoryDir objects in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategoryDir
    ).order_by(
        model.HostCategoryDir.id
    )

    return query.all()


def get_host_category_by_hostid_category(session, host_id, category):
    ''' Return all HostCategory having the specified host_id and category.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategory
    ).filter(
        model.HostCategory.host_id == host_id
    ).filter(
        model.HostCategory.category_id == model.Category.id
    ).filter(
        model.Category.name == category
    )

    return query.all()


def get_host_category_url_by_id(session, host_category_url_id):
    ''' Return a specified HostCategoryUrl via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategoryUrl
    ).filter(
        model.HostCategoryUrl.id == host_category_url_id
    )

    return query.first()


def get_host_category_url(session):
    ''' Return all HostCategoryUrl in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategoryUrl
    ).order_by(
        model.HostCategoryUrl.id
    )

    return query.all()


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


def get_country_continent_redirect(session):
    ''' Return all the CountryContinentRedirect present in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.CountryContinentRedirect
    ).order_by(
        model.CountryContinentRedirect.id
    )

    return query.all()


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


def get_version_by_id(session, v_id):
    ''' Return a specified Version given its identifier in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Version
    ).filter(
        model.Version.id == v_id
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


def get_category_by_name(session, name):
    ''' Return the category present in the database with the specifie name.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Category
    ).filter(
        model.Category.name == name
    )

    return query.first()


def get_category_directory(session):
    ''' Return all the category directory present in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.CategoryDirectory
    ).order_by(
        model.CategoryDirectory.directory_id
    )
    return query.all()


def get_product_by_name(session, p_name):
    ''' Return a product by its name.

    :arg session: the session with which to connect to the database.
    :arg p_name: the product name to find in the database

    '''
    query = session.query(
        model.Product
    ).filter(
        model.Product.name == p_name
    ).order_by(
        model.Product.name
    )

    return query.first()


def get_products(session, publiclist=None):
    ''' Return the list of all the products in the database.

    :arg session: the session with which to connect to the database.
    :arg publiclist: if the result should be filtered by the publiclist column

    '''
    query = session.query(
        model.Product
    ).order_by(
        model.Product.name
    )

    if publiclist is not None:
        query = query.filter(model.Product.publiclist == publiclist)

    return query.all()


def get_repo_prefix_arch(session, prefix, arch):
    ''' Return a repository by its prefix and arch.

    :arg session: the session with which to connect to the database.
    :arg prefix: the prefix of the repository
    :arg arch: the arch of the repository

    '''
    query = session.query(
        model.Repository
    ).filter(
        model.Repository.prefix == prefix
    ).filter(
        model.Repository.arch_id == model.Arch.id
    ).filter(
        model.Arch.name == arch
    )

    return query.first()


def get_repo_by_name(session, name):
    ''' Return a repository by its name.

    :arg session: the session with which to connect to the database.
    :arg name: the name of the repository

    '''
    query = session.query(
        model.Repository
    ).filter(
        model.Repository.name == name
    )

    return query.first()


def get_repo_by_dir(session, path):
    ''' Return repositories by the path of its directory.

    :arg session: the session with which to connect to the database.
    :arg path: the path of the directory linked to the repositories returned

    '''
    query = session.query(
        model.Repository
    ).filter(
        model.Repository.directory_id == model.Directory.id
    ).filter(
        model.Directory.name == path
    ).order_by(
        model.Repository.id
    )

    return query.all()


def get_repositories(session):
    ''' Return all repositories in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Repository
    ).order_by(
        model.Repository.id
    )

    return query.all()


def get_reporedirect(session):
    ''' Return all reporedirect in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.RepositoryRedirect
    ).order_by(
        model.RepositoryRedirect.id
    )

    return query.all()


def get_arches(session, publiclist=None):
    ''' Return the list of all the arch in the database.

    :arg session: the session with which to connect to the database.
    :arg publiclist: if the result should be filtered by the publiclist column

    '''
    query = session.query(
        model.Arch
    ).order_by(
        model.Arch.name
    )

    if publiclist is not None:
        query = query.filter(model.Arch.publiclist == publiclist)

    return query.all()


def add_admin_to_site(session, site, admin):
    ''' Add an admin to the specified site.

    :arg session: the session with which to connect to the database.

    '''

    site_id = site.id

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


def get_locations(session):
    ''' Return all locations in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Location
    ).order_by(
        model.Location.id
    )

    return query.all()


def get_netblock_country(session):
    ''' Return all NetblockCountry in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.NetblockCountry
    ).order_by(
        model.NetblockCountry.id
    )

    return query.all()


def get_mirrors(
        session, private=None, internet2=None, internet2_clients=None,
        asn_clients=None, admin_active=None, user_active=None, urls=None,
        last_crawl_duration=False, last_checked_in=False, last_crawled=False,
        site_private=None, site_admin_active=None, site_user_active=None,
        up2date=None, host_category_url_private=None,
        version_id=None, arch_id=None, order_by_crawl_duration=False,
        product_id=None):
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

    if product_id is not None:
        query = query.filter(
            model.Host.id == model.HostCategory.host_id
        ).filter(
            model.HostCategory.category_id == model.Category.id
        ).filter(
            model.Category.product_id == product_id
        )

    final_query = session.query(
        model.Host
    ).filter(
        model.Host.id.in_(query.subquery())
    )

    if order_by_crawl_duration is True:
        # for best crawling results, start with the slowest mirrors
        final_query = final_query.order_by(model.Host.last_crawl_duration.desc())
    else:
        # default order
        final_query = final_query.order_by(model.Host.country, model.Host.name)

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


def get_file_detail(
        session, filename, directory_id, md5=False, sha1=False, sha256=False,
        sha512=False, size=False, timestamp=False, reverse=False):
    ''' Return a specified FileDetail having the corresponding details.

    :arg session: the session with which to connect to the database.
    :arg filename:
    :arg directory_id:
    :kwarg md5:
    :kwarg sha1:
    :kwarg sha256:
    :kwarg sha512:
    :kwarg size:
    :kwarg timestamp:

    '''
    query = session.query(
        model.FileDetail
    ).filter(
        model.FileDetail.filename == filename
    ).filter(
        model.FileDetail.directory_id == directory_id
    )

    if md5 is not False:
        query = query.filter(model.FileDetail.md5 == md5)

    if sha1 is not False:
        query = query.filter(model.FileDetail.sha1 == sha1)

    if sha256 is not False:
        query = query.filter(model.FileDetail.sha256 == sha256)

    if sha512 is not False:
        query = query.filter(model.FileDetail.sha512 == sha512)

    if size is not False:
        query = query.filter(model.FileDetail.size == size)

    if timestamp is not False:
        query = query.filter(model.FileDetail.timestamp == timestamp)

    if reverse is True:
        # This should return the newest file
        query = query.order_by(model.FileDetail.id.desc())

    return query.first()


def get_file_details(session):
    ''' Return all the FileDetail object in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.FileDetail
    ).order_by(
        model.FileDetail.id
    )

    return query.all()


def get_directories(session):
    ''' Return all Directory in the database.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Directory
    ).order_by(
        model.Directory.id
    )

    return query.all()


def get_directory_by_id(session, id):
    ''' Return a specified Directory via its identifier.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Directory
    ).filter(
        model.Directory.id == id
    )

    return query.first()


def get_hostcategorydir_by_hostcategoryid(session, host_category_id):
    ''' Return all HostCategoryDir via its host_category_id.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.HostCategoryDir
    ).filter(
        model.HostCategoryDir.host_category_id == host_category_id
    )

    return query.all()


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


def uploaded_config(session, host, config):
    ''' Update the configuration of a specific host. '''
    message = ''

    def _config_categories(config):
        noncategories = ['version', 'global', 'site', 'host', 'stats']
        if config is not None:
            return [
                key
                for key in config.keys()
                if key not in noncategories
            ]
        else:
            return []

    def compare_dir(hcdir, files):
        if hcdir.directory is None or hcdir.directory.files is None:
            raise Exception
        dfiles = hcdir.directory.files
        if len(dfiles) == 0 and len(files) == 0:
            return True
        for fname, fdata in dfiles.items():
            if fname not in files:
                return False
            if fdata['size'] != files[fname]:
                return False
        return True

    # fill in the host category data (HostCategory and HostCategoryURL)
    # the category names in the config have been lowercased
    # so we have to find the matching mixed-case category name.

    for cat_name in _config_categories(config):
        if 'dirtree' not in config[cat_name]:
            # The received report_mirror data is missing
            # the actual data. Pretty unlikely, but possible.
            continue

        hc = None
        for cat in host.categories:
            if cat.category.name.lower() == cat_name.lower():
                hc = cat
                break

        if hc is None:
            # Only accept entries for existing HostCategories.
            # Don't let report_mirror create HostCategories
            # it must be done through the web UI.
            continue

        marked_up2date = 0
        deleted = 0
        added = 0
        # and now one HostCategoryDir for each dir in the dirtree
        for dirname,files in config[cat_name]['dirtree'].items():
            d = dirname.strip('/')
            hcdir = get_hostcategorydir_by_hostcategoryid_and_path(
                session, host_category_id=hc.id, path=d)
            if hcdir:
                hcdir = hcdir[0]
                # This is evil, but it avoids stat()s on the client
                # side and a lot of data uploading.
                # A directory is considered up to date if it exists
                # on the client and in the database.
                # In contrast to report_mirror the crawler also
                # checks for the actual files in the directory.
                marked_up2date += 1
                if hcdir.up2date != True:
                    hcdir.up2date = True
                    session.add(hcdir)
                    session.commit()
            else:
                if len(d) > 0:
                    dname = "%s/%s" % (hc.category.topdir.name, d)
                else:
                    dname = hc.category.topdir.name

                # Don't create an entry for a directory the database
                # doesn't know about and if a crawler created it so we
                # hit a unique violation, then we don't have to
                try:
                    directory = get_directory_by_name(session, dname)
                    hcdir = model.HostCategoryDir(
                        host_category_id=hc.id,
                        path=d,
                        directory_id=directory.id)
                    session.add(hcdir)
                    session.commit()
                    added += 1
                except:
                    pass

        for hcdir in get_hostcategorydir_by_hostcategoryid(session, hc.id):
            # handle disappearing hcdirs, deleted by other processes
            try:
                hcdirpath = hcdir.path
            except: continue
            if hcdirpath not in config[cat_name]['dirtree'].keys():
                try:
                    session.delete(hcdir)
                    session.commit()
                except:
                    pass
                deleted += 1

        message += "Category %s directories updated: %s  added: %s  deleted %s\n" % (cat.category.name, marked_up2date, added, deleted)
        host.last_checked_in = datetime.datetime.utcnow()
        session.add(hc)
        session.commit()

    return message


def query_directories(session):
    ''' Return the list of Directory, Host, HostCategoryUrl and Site
    information required by `refresh_mirrorlist_cache` to build the pickle
    file.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Directory.id.label('directory_id'),
        model.Directory.name.label('dname'),
        model.Host.id.label('hostid'),
        model.Host.country.label('country'),
        model.HostCategoryUrl.id.label('id'),
        model.Site.private.label('siteprivate'),
        model.Host.private.label('hostprivate'),
        model.Host.internet2.label('internet2'),
        model.Host.internet2_clients.label('internet2_clients'),
    ).filter(
        model.Host.user_active == True
    ).filter(
        model.Host.admin_active == True
    ).filter(
        model.Host.site_id == model.Site.id
    ).filter(
        model.Site.user_active == True
    ).filter(
        model.Site.admin_active == True
    ).filter(
        model.Host.id == model.HostCategory.host_id
    ).filter(
        model.HostCategory.category_id == model.CategoryDirectory.category_id
    ).filter(
        model.CategoryDirectory.directory_id == model.Directory.id
    ).filter(
        model.HostCategory.id == model.HostCategoryUrl.host_category_id
    ).filter(
        model.HostCategoryUrl.private == False
    )

    q1 = query.filter(
        model.HostCategoryDir.host_category_id == model.HostCategory.id
    ).filter(
        model.HostCategoryDir.directory_id == model.Directory.id
    ).filter(
        model.HostCategoryDir.up2date == True
    )

    q2 = query.filter(
        model.HostCategory.always_up2date == True
    )

    q = session.query(
        q1.union(q2).subquery()
    ).order_by(
        'dname',
        'hostid'
    )

    return q.all()


def get_directory_exclusive_host(session):
    ''' Return the list of Directory that are exclusive for some hosts.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.Directory.name.label('dname'),
        model.DirectoryExclusiveHost.host_id.label('host_id')
    ).filter(
        model.Directory.id == model.DirectoryExclusiveHost.directory_id
    ).order_by(
        'dname'
    )

    return query.all()


def get_rsync_filter_directories(session, categories, since):
    ''' Return the list of directory that were updated.

    :arg session: the session with which to connect to the database.
    :arg categories: a list of category names.
    :arg since: timestamp.

    '''

    try:
        since = int(since)
    except:
        return []

    if len(categories) == 0:
        return []

    query = session.query(
        model.Directory.name
    ).filter(
        model.Directory.id == model.CategoryDirectory.directory_id
    ).filter(
        model.CategoryDirectory.category_id == model.Category.id
    ).filter(
        model.Category.name.in_(categories)
    ).filter(
        model.Directory.ctime > since
    )

    result = [entry[0] for entry in query.all()]
    return result
