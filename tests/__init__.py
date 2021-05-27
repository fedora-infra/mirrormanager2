# -*- coding: utf-8 -*-

'''
mirrormanager2 tests.
'''

from __future__ import print_function

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import datetime
import logging
import unittest
import sys
import os

from contextlib import contextmanager
from flask import appcontext_pushed, g
from mirrormanager2.app import APP, FAS, LOG
from mirrormanager2.lib import model

# DB_PATH = 'sqlite:///:memory:'
# A file database is required to check the integrity, don't ask
DB_PATH = 'sqlite:////tmp/test.sqlite'
FAITOUT_URL = 'http://faitout.fedorainfracloud.org/'

if os.environ.get('BUILD_ID'):
    try:
        import requests
        req = requests.get('%s/new' % FAITOUT_URL)
        if req.status_code == 200:
            DB_PATH = req.text
            print('Using faitout at: %s' % DB_PATH)
    except:
        pass

LOG.handlers = []


@contextmanager
def user_set(APP, user):
    """ Set the provided user as fas_user in the provided application."""

    # Hack used to remove the before_request function set by
    # flask_fas_openid.FAS which otherwise kills our effort to set a
    # flask.g.fas_user.
    APP.before_request_funcs[None] = []

    def handler(sender, **kwargs):
        g.fas_user = user

    with appcontext_pushed.connected_to(handler, APP):
        yield


class FakeFasUser(object):
    """ Fake FAS user used for the tests. """
    id = 100
    username = 'pingou'
    cla_done = True
    groups = ['packager', 'signed_fpca']
    bugzilla_email = 'pingou@fp.o'


class AnotherFakeFasUser(object):
    """ Fake FAS user used for the tests. """
    id = 110
    username = 'kevin'
    cla_done = True
    groups = ['packager', 'signed_fpca']
    bugzilla_email = 'kevin@fp.o'
    signed_fpca = True


class FakeFasUserAdmin(object):
    """ Fake FAS user used for the tests. """
    id = 1000
    username = 'admin'
    cla_done = True
    groups = ['packager', 'sysadmin-main', 'signed_fpca']


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every test. """
        if '///' in DB_PATH:
            dbfile = DB_PATH.split('///')[1]
            if os.path.exists(dbfile):
                os.unlink(dbfile)
        self.session = model.create_tables(DB_PATH, debug=False)
        APP.logger.handlers = []
        APP.logger.setLevel(logging.CRITICAL)
        APP.before_request(FAS._check_session)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        if '///' in DB_PATH:
            dbfile = DB_PATH.split('///')[1]
            if os.path.exists(dbfile):
                os.unlink(dbfile)

        self.session.rollback()
        self.session.close()

        #if DB_PATH.startswith('postgres'):
            #if 'localhost' in DB_PATH:
                #model.drop_tables(DB_PATH, self.session.bind)
            #else:
                #db_name = DB_PATH.rsplit('/', 1)[1]
                #req = requests.get(
                    #'%s/clean/%s' % (FAITOUT_URL, db_name))
                #print req.text


def create_base_items(session):
    ''' Insert some base information in the database.
    '''
    # Insert some Arch
    item = model.Arch(
        name='source',
        publiclist=False,
        primary_arch=False,
    )
    session.add(item)
    item = model.Arch(
        name='i386',
        publiclist=True,
        primary_arch=True,
    )
    session.add(item)
    item = model.Arch(
        name='x86_64',
        publiclist=True,
        primary_arch=True,
    )
    session.add(item)
    item = model.Arch(
        name='ppc',
        publiclist=True,
        primary_arch=False,
    )
    session.add(item)

    # Insert some Country
    item = model.Country(
        code='FR',
    )
    session.add(item)
    item = model.Country(
        code='US',
    )
    session.add(item)

    # Insert some Product
    item = model.Product(
        name='EPEL',
        publiclist=True,
    )
    session.add(item)
    item = model.Product(
        name='Fedora',
        publiclist=True,
    )
    session.add(item)

    # Insert some CountryContinentRedirect
    item = model.CountryContinentRedirect(
        country='IL',
        continent='EU',
    )
    session.add(item)
    item = model.CountryContinentRedirect(
        country='AM',
        continent='EU',
    )
    session.add(item)
    item = model.CountryContinentRedirect(
        country='JO',
        continent='EU',
    )
    session.add(item)

    # Insert some User
    item = model.User(
        user_name='pingou',
        email_address='pingou@fp.o',
        display_name='pingou',
        password='foo',
    )
    session.add(item)
    item = model.User(
        user_name='kevin',
        email_address='kevin@fp.o',
        display_name='kevin',
        password='foo2',
    )
    session.add(item)
    item = model.User(
        user_name='ralph',
        email_address='ralph@fp.o',
        display_name='ralph',
        password='foo3',
    )
    session.add(item)
    item = model.User(
        user_name='shaiton',
        email_address='shaiton@fp.o',
        display_name='shaiton',
        password='foo4',
        token='bar',
    )
    session.add(item)

    # Insert some UserVisit
    item = model.UserVisit(
        user_id=1,
        visit_key='foo',
        user_ip='127.0.0.1',
        expiry=datetime.datetime.utcnow() + datetime.timedelta(days=1)
    )
    session.add(item)

    session.commit()


def create_site(session):
    ''' Create some site to play with for the tests
    '''
    item = model.Site(
        name='test-mirror',
        password='test_password',
        org_url='http://fedoraproject.org',
        private=False,
        admin_active=True,
        user_active=True,
        all_sites_can_pull_from_me=True,
        downstream_comments='Mirror available over RSYNC and HTTP.',
        email_on_drop=False,  # Default value - not changeable in the UI Oo
        email_on_add=False,  # Default value - not changeable in the UI Oo
        created_by='pingou',
    )
    session.add(item)
    item = model.Site(
        name='test-mirror2',
        password='test_password2',
        org_url='http://getfedora.org',
        private=False,
        admin_active=True,
        user_active=True,
        all_sites_can_pull_from_me=True,
        downstream_comments='Mirror available over HTTP.',
        email_on_drop=False,
        email_on_add=False,
        created_by='kevin',
    )
    session.add(item)
    item = model.Site(
        name='test-mirror_private',
        password='test_password_private',
        org_url='http://192.168.0.15',
        private=True,
        admin_active=True,
        user_active=True,
        all_sites_can_pull_from_me=False,
        downstream_comments='My own mirror available over HTTP.',
        email_on_drop=False,
        email_on_add=False,
        created_by='skvidal',
    )
    session.add(item)

    session.commit()


def create_site_admin(session):
    ''' Create some site admins to play with for the tests
    '''
    item = model.SiteAdmin(
        username='ralph',
        site_id=1,
    )
    session.add(item)
    item = model.SiteAdmin(
        username='kevin',
        site_id=1,
    )
    session.add(item)

    item = model.SiteAdmin(
        username='ralph',
        site_id=2,
    )
    session.add(item)
    item = model.SiteAdmin(
        username='pingou',
        site_id=2,
    )
    session.add(item)

    item = model.SiteAdmin(
        username='shaiton',
        site_id=3,
    )
    session.add(item)

    session.commit()


def create_hosts(session):
    ''' Create some hosts to play with for the tests
    '''
    item = model.Host(
        name='mirror.localhost',
        site_id=1,
        robot_email=None,
        admin_active=True,
        user_active=True,
        country='US',
        bandwidth_int=100,
        comment=None,
        private=False,
        internet2=False,
        internet2_clients=False,
        asn=None,
        asn_clients=False,
        max_connections=10,
    )
    session.add(item)
    item = model.Host(
        name='mirror2.localhost',
        site_id=2,
        robot_email=None,
        admin_active=True,
        user_active=True,
        country='FR',
        bandwidth_int=100,
        comment=None,
        private=False,
        internet2=False,
        internet2_clients=False,
        asn=100,
        asn_clients=True,
        max_connections=10,
    )
    session.add(item)
    item = model.Host(
        name='private.localhost',
        site_id=1,
        robot_email=None,
        admin_active=True,
        user_active=True,
        country='NL',
        bandwidth_int=100,
        comment='My own private mirror',
        private=True,
        internet2=False,
        internet2_clients=False,
        asn=None,
        asn_clients=False,
        max_connections=10,
    )
    session.add(item)

    session.add(item)
    item = model.Host(
        name='Another test entry',
        site_id=3,
        robot_email=None,
        admin_active=True,
        user_active=True,
        country='HR',
        bandwidth_int=300,
        comment='Public mirror',
        private=False,
        internet2=False,
        internet2_clients=False,
        asn=None,
        asn_clients=False,
        max_connections=10,
    )
    session.add(item)

    session.commit()


def create_host_country_allowed(session):
    item = model.HostCountryAllowed(
        country='HR',
        host_id=4,
    )
    session.add(item)
    item = model.HostCountryAllowed(
        country='US',
        host_id=4,
    )
    session.add(item)
    session.commit()

def create_hostaclip(session):
    ''' Create some HostAclIp to play with for the tests
    '''
    item = model.HostAclIp(
        ip='85.12.0.250',
        host_id=1,
    )
    session.add(item)

    item = model.HostAclIp(
        ip='192.168.0.12',
        host_id=2,
    )
    session.add(item)

    session.commit()


def create_directory(session):
    ''' Create some Directory to play with for the tests
    '''
    item = model.Directory(
        name='pub/fedora/linux',
        readable=True,
    )
    session.add(item)

    item = model.Directory(
        name='pub/fedora/linux/extras',
        readable=True,
    )
    session.add(item)

    item = model.Directory(
        name='pub/epel',
        readable=True,
    )
    session.add(item)

    item = model.Directory(
        name='pub/fedora/linux/releases/26',
        readable=True,
    )
    session.add(item)

    item = model.Directory(
        name='pub/fedora/linux/releases/27',
        readable=True,
    )
    session.add(item)

    item = model.Directory(
        name='pub/archive/fedora/linux/releases/26/Everything/source',
        readable=True,
    )
    session.add(item)

    item = model.Directory(
        name='pub/fedora/linux/updates/testing/25/x86_64',
        readable=True,
    )
    session.add(item)
    item = model.Directory(
        name='pub/fedora/linux/updates/testing/26/x86_64',
        readable=True,
    )
    session.add(item)
    item = model.Directory(
        name='pub/fedora/linux/updates/testing/27/x86_64',
        readable=True,
    )
    session.add(item)

    session.commit()


def create_category(session):
    ''' Create some Category to play with for the tests
    '''
    item = model.Category(
        name='Fedora Linux',
        product_id=2,
        canonicalhost='http://download.fedora.redhat.com',
        topdir_id=1,
        publiclist=True
    )
    session.add(item)

    item = model.Category(
        name='Fedora EPEL',
        product_id=1,
        canonicalhost='http://dl.fedoraproject.org',
        topdir_id=2,
        publiclist=True
    )
    session.add(item)

    session.commit()


def create_hostcategory(session):
    ''' Create some HostCategory to play with for the tests
    '''
    item = model.HostCategory(
        host_id=1,
        category_id=1,
        always_up2date=True,
    )
    session.add(item)
    item = model.HostCategory(
        host_id=1,
        category_id=2,
        always_up2date=True,
    )
    session.add(item)

    item = model.HostCategory(
        host_id=2,
        category_id=1,
        always_up2date=False,
    )
    session.add(item)
    item = model.HostCategory(
        host_id=2,
        category_id=2,
        always_up2date=False,
    )
    session.add(item)

    session.commit()


def create_hostcategoryurl(session):
    ''' Create some HostCategoryUrl to play with for the tests
    '''
    item = model.HostCategoryUrl(
        host_category_id=1,
        url='http://infrastructure.fedoraproject.org/pub/fedora/linux',
        private=False,
    )
    session.add(item)
    item = model.HostCategoryUrl(
        host_category_id=1,
        url='http://infrastructure.fedoraproject.org/pub/epel',
        private=False,
    )
    session.add(item)

    item = model.HostCategoryUrl(
        host_category_id=1,
        url='http://dl.fedoraproject.org/pub/fedora/linux',
        private=False,
    )
    session.add(item)
    item = model.HostCategoryUrl(
        host_category_id=1,
        url='http://dl.fedoraproject.org/pub/epel',
        private=False,
    )
    session.add(item)

    item = model.HostCategoryUrl(
        host_category_id=3,
        url='https://infrastructure.fedoraproject.org/pub/fedora/linux',
        private=False,
    )
    session.add(item)
    item = model.HostCategoryUrl(
        host_category_id=3,
        url='https://infrastructure.fedoraproject.org/pub/epel',
        private=False,
    )
    session.add(item)

    item = model.HostCategoryUrl(
        host_category_id=3,
        url='https://dl.fedoraproject.org/pub/fedora/linux',
        private=False,
    )
    session.add(item)
    item = model.HostCategoryUrl(
        host_category_id=3,
        url='https://dl.fedoraproject.org/pub/epel',
        private=False,
    )
    session.add(item)

    session.commit()


def create_categorydirectory(session):
    ''' Create some CategoryDirectory to play with for the tests
    '''
    item = model.CategoryDirectory(
        directory_id=1,
        category_id=1,
    )
    session.add(item)
    item = model.CategoryDirectory(
        directory_id=4,
        category_id=1,
    )
    session.add(item)
    item = model.CategoryDirectory(
        directory_id=5,
        category_id=1,
    )
    session.add(item)

    item = model.CategoryDirectory(
        directory_id=3,
        category_id=2,
    )
    session.add(item)

    session.commit()


def create_hostnetblock(session):
    ''' Create some HostNetblock to play with for the tests
    '''
    item = model.HostNetblock(
        host_id=3,
        netblock='192.168.0.0/24',
        name='home',
    )
    session.add(item)

    session.commit()


def create_hostpeerasn(session):
    ''' Create some HostPeerAsn to play with for the tests
    '''
    item = model.HostPeerAsn(
        host_id=3,
        asn='25640',
        name='Hawaii',
    )
    session.add(item)

    session.commit()


def create_hostcountry(session):
    ''' Create some HostCountry to play with for the tests
    '''
    item = model.HostCountry(
        host_id=1,
        country_id=2,
    )
    session.add(item)
    item = model.HostCountry(
        host_id=2,
        country_id=1,
    )
    session.add(item)

    session.commit()


def create_version(session):
    ''' Create some Version to play with for the tests
    '''
    item = model.Version(
        name=26,
        product_id=2,
        is_test=False,
        display=True,
        ordered_mirrorlist=True,
    )
    session.add(item)
    item = model.Version(
        name='27-alpha',
        product_id=2,
        is_test=True,
        display=False,
        ordered_mirrorlist=True,
    )
    session.add(item)
    item = model.Version(
        name=27,
        product_id=2,
        is_test=False,
        display=True,
        ordered_mirrorlist=True,
    )
    session.add(item)
    item = model.Version(
        name='development',
        product_id=2,
        is_test=False,
        display=True,
        display_name='rawhide',
        ordered_mirrorlist=True,
    )
    session.add(item)
    item = model.Version(
        name=25,
        product_id=2,
        is_test=False,
        display=True,
        ordered_mirrorlist=True,
    )
    session.add(item)

    item = model.Version(
        name=7,
        product_id=1,
        is_test=False,
        display=True,
        ordered_mirrorlist=True,
    )
    session.add(item)

    session.commit()


def create_repository(session):
    ''' Create some Repository to play with for the tests
    '''
    item = model.Repository(
        name='pub/fedora/linux/updates/testing/25/x86_64',
        prefix='updates-testing-f25',
        category_id=1,
        version_id=5,
        arch_id=3,
        directory_id=7,
        disabled=True
    )
    session.add(item)
    item = model.Repository(
        name='pub/fedora/linux/updates/testing/26/x86_64',
        prefix='updates-testing-f26',
        category_id=1,
        version_id=1,
        arch_id=3,
        directory_id=8,
        disabled=False
    )
    session.add(item)
    item = model.Repository(
        name='pub/fedora/linux/updates/testing/27/x86_64',
        prefix='updates-testing-f27',
        category_id=1,
        version_id=3,
        arch_id=3,
        directory_id=9,
        disabled=False
    )
    session.add(item)
    item = model.Repository(
        name='pub/fedora/linux/updates/27/x86_64',
        prefix='updates-released-f27',
        category_id=1,
        version_id=3,
        arch_id=3,
        directory_id=5,
        disabled=False
    )
    session.add(item)

    session.commit()


def create_repositoryredirect(session):
    ''' Create some RepositoryRedirect to play with for the tests
    '''
    item = model.RepositoryRedirect(
        from_repo='fedora-rawhide',
        to_repo='rawhide',
    )
    session.add(item)
    item = model.RepositoryRedirect(
        from_repo='fedora-install-rawhide',
        to_repo='rawhide',
    )
    session.add(item)
    item = model.RepositoryRedirect(
        from_repo='epel-6.0',
        to_repo='epel-6',
    )
    session.add(item)

    session.commit()


def create_location(session):
    ''' Create some Location to play with for the tests
    '''
    item = model.Location(
        name='foo',
    )
    session.add(item)
    item = model.Location(
        name='bar',
    )
    session.add(item)
    item = model.Location(
        name='foobar',
    )
    session.add(item)

    session.commit()


def create_netblockcountry(session):
    ''' Create some NetblockCountry to play with for the tests
    '''
    item = model.NetblockCountry(
        netblock='127.0.0.0/24',
        country='AU',
    )
    session.add(item)

    session.commit()


def create_hostcategorydir(session):
    ''' Create some HostCategoryDir to play with for the tests
    '''
    item = model.HostCategoryDir(
        host_category_id=1,
        directory_id=4,
        path='pub/fedora/linux/releases/26',
        up2date=True,
    )
    session.add(item)
    item = model.HostCategoryDir(
        host_category_id=3,
        directory_id=5,
        path='pub/fedora/linux/releases/27',
        up2date=True,
    )
    session.add(item)

    session.commit()


def create_hostcategorydir_one_more(session):
    item = model.HostCategoryDir(
        host_category_id=3,
        directory_id=8,
        path='pub/fedora/linux/updates/testing/26/x86_64',
        up2date=True,
    )
    session.add(item)

    session.commit()

def create_hostcategorydir_even_more(session):
    item = model.HostCategoryDir(
        host_category_id=3,
        directory_id=9,
        path='pub/fedora/linux/updates/testing/27/x86_64',
        up2date=True,
    )
    session.add(item)

    session.commit()

def create_directoryexclusivehost(session):
    ''' Create some DirectoryExclusiveHost to play with for the tests
    '''
    item = model.DirectoryExclusiveHost(
        host_id=1,
        directory_id=4,
    )
    session.add(item)
    item = model.DirectoryExclusiveHost(
        host_id=3,
        directory_id=5,
    )
    session.add(item)

    session.commit()


def create_filedetail(session):
    ''' Create some FileDetail to play with for the tests
    '''
    item = model.FileDetail(
        filename='repomd.xml',
        directory_id=4,
        timestamp=1351758825,
        size=2972,
        sha1='foo_sha1',
        md5='foo_md5',
        sha256='foo_sha256',
        sha512='foo_sha512',
    )
    session.add(item)
    item = model.FileDetail(
        filename='repomd.xml',
        directory_id=7,
        timestamp=1357758825,
        size=2971,
        sha1='foo_sha1',
        md5='foo_md5',
        sha256='foo_sha256',
        sha512='foo_sha512',
    )
    session.add(item)
    item = model.FileDetail(
        filename='repomd.xml',
        directory_id=8,
        timestamp=1357758826,
        size=2972,
        sha1='foo2_sha1',
        md5='foo2_md5',
        sha256='foo2_sha256',
        sha512='foo2_sha512',
    )
    session.add(item)
    item = model.FileDetail(
        filename='repomd.xml',
        directory_id=9,
        timestamp=1357758827,
        size=2973,
        sha1='foo3_sha1',
        md5='foo3_md5',
        sha256='foo3_sha256',
        sha512='foo3_sha512',
    )
    session.add(item)

    session.commit()


def create_user_groups(session):
    ''' Create some Grouip and UserGroup to play with for the tests
    '''
    item = model.Group(
        group_name='fpca',
        display_name='Fedora Project Contributor Agreement',
    )
    session.add(item)
    item = model.Group(
        group_name='packager',
        display_name='Fedora Packagers',
    )
    session.add(item)

    session.commit()

    item = model.UserGroup(
        user_id=1,
        group_id=1,
    )
    session.add(item)
    item = model.UserGroup(
        user_id=2,
        group_id=1,
    )
    session.add(item)
    item = model.UserGroup(
        user_id=3,
        group_id=1,
    )
    session.add(item)
    item = model.UserGroup(
        user_id=4,
        group_id=1,
    )
    session.add(item)

    item = model.UserGroup(
        user_id=1,
        group_id=2,
    )
    session.add(item)
    item = model.UserGroup(
        user_id=2,
        group_id=2,
    )
    session.add(item)
    item = model.UserGroup(
        user_id=4,
        group_id=2,
    )
    session.add(item)

    session.commit()


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
