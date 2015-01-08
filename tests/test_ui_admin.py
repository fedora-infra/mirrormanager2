# -*- coding: utf-8 -*-

'''
mirrormanager2 tests for the Flask UI Admin controller.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest
import sys
import os

from mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import mirrormanager2.admin
import mirrormanager2.app
from mirrormanager2.lib import model
import tests


class FlaskUiAdminTest(tests.Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskUiAdminTest, self).setUp()

        mirrormanager2.app.APP.config['TESTING'] = True
        mirrormanager2.app.SESSION = self.session
        mirrormanager2.app.ADMIN.SESSION = self.session
        mirrormanager2.app.APP.SESSION = self.session
        mirrormanager2.admin.SESSION = self.session
        mirrormanager2.admin.ADMIN.SESSION = self.session
        mirrormanager2.admin.APP.SESSION = self.session
        for view in mirrormanager2.admin.VIEWS:
            view.session = self.session
        self.app = mirrormanager2.app.APP.test_client()

        # Fill the DB a little bit
        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_site_admin(self.session)
        tests.create_hosts(self.session)
        tests.create_location(self.session)
        tests.create_netblockcountry(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategoryurl(self.session)
        tests.create_hostcategorydir(self.session)
        tests.create_categorydirectory(self.session)
        tests.create_version(self.session)
        tests.create_repository(self.session)
        tests.create_repositoryredirect(self.session)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin(self, login_func):
        """ Test the admin function. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Home - Admin</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_arch(self, login_func):
        """ Test the admin Arch view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/archview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Arch - Admin</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/?sort=0" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (4)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_category(self, login_func):
        """ Test the admin Category view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/categoryview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Category - Admin</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/?sort=2" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (2)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_country(self, login_func):
        """ Test the admin Country view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/countryview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Country - Country - Admin</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/countryview/?sort=0" '
                'title="Sort by Code">Code</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (2)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_countrycontinentredirectview(self, login_func):
        """ Test the admin CountryContinentRedirect view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/countrycontinentredirectview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Country - Country Continent Redirect - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/countrycontinentredirectview/?sort=0" '
                'title="Sort by Country">Country</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_embargoedcountryview(self, login_func):
        """ Test the admin EmbargoedCountry view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/embargoedcountryview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Country - Embargoed Country - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/embargoedcountryview/?sort=0" '
                'title="Sort by Country Code">Country Code</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_directoryview(self, login_func):
        """ Test the admin Directory view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/directoryview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Directory - Directory - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/directoryview/?sort=0" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (9)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_directoryexclusivehostview(self, login_func):
        """ Test the admin DirectoryExclusiveHost view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/directoryexclusivehostview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Directory - Directory Exclusive Host - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertEqual(
                output.data.count('<th class="column-header">'), 3)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_filedetailview(self, login_func):
        """ Test the admin FileDetail view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/filedetailview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>File - File Detail - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/filedetailview/?sort=1" '
                'title="Sort by Filename">Filename</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_filedetailfilegroupview(self, login_func):
        """ Test the admin FileDetailFileGroup view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/filedetailfilegroupview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>File - File Detail File Group - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertEqual(
                output.data.count('<th class="column-header">'), 0)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_filegroupview(self, login_func):
        """ Test the admin FileGroup view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/filegroupview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>File - File Group - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/filegroupview/?sort=0" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostview(self, login_func):
        """ Test the admin Host view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hostview/?sort=1" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostaclipview(self, login_func):
        """ Test the admin Host Acl Ip view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostaclipview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Acl Ip - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hostaclipview/?sort=1" '
                'title="Sort by Ip">Ip</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcategoryview(self, login_func):
        """ Test the admin Host Category view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostcategoryview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Category - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hostcategoryview/?sort=2" '
                'title="Sort by Always Up2Date">Always Up2Date</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (4)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcategorydirview(self, login_func):
        """ Test the admin Host Category Dir view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostcategorydirview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Category Dir - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hostcategorydirview/?sort=2" '
                'title="Sort by Path">Path</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (2)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcategoryurlview(self, login_func):
        """ Test the admin Host Category Url view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostcategoryurlview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Category Url - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hostcategoryurlview/?sort=1" '
                'title="Sort by Url">Url</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (4)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcountryview(self, login_func):
        """ Test the admin Host Country view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostcountryview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Country - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertEqual(
                output.data.count('<th class="column-header">'), 2)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcountryallowedview(self, login_func):
        """ Test the admin Host Country Allowed view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostcountryallowedview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Country Allowed - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hostcountryallowedview/?sort=1" '
                'title="Sort by Country">Country</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostlocationview(self, login_func):
        """ Test the admin Host Location view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostlocationview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Location - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertEqual(
                output.data.count('<th class="column-header">'), 2)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostnetblockview(self, login_func):
        """ Test the admin Host Netblock view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostnetblockview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Netblock - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hostnetblockview/?sort=2" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostpeerasnview(self, login_func):
        """ Test the admin Host Peer Asn view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hostpeerasnview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Peer Asn - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hostpeerasnview/?sort=2" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hoststatsview(self, login_func):
        """ Test the admin Host Stats view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/hoststatsview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Host - Host Stats - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/hoststatsview/?sort=2" '
                'title="Sort by Type">Type</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_locationview(self, login_func):
        """ Test the admin Location view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/locationview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Location - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/locationview/?sort=0" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_netblockcountryview(self, login_func):
        """ Test the admin Netblock Country view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/netblockcountryview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Netblock Country - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/netblockcountryview/?sort=0" '
                'title="Sort by Netblock">Netblock</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (1)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_productview(self, login_func):
        """ Test the admin Product view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/productview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Product - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/productview/?sort=0" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (2)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_repositoryview(self, login_func):
        """ Test the admin Repository view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/repositoryview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Repository - Repository - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/repositoryview/?sort=4" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_repositoryredirectview(self, login_func):
        """ Test the admin Repository Redirect view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/repositoryredirectview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Repository - Repository Redirect - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/repositoryredirectview/?sort=0" '
                'title="Sort by To Repo">To Repo</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_siteview(self, login_func):
        """ Test the admin Site view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/siteview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Site - Site - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/siteview/?sort=0" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_siteadminview(self, login_func):
        """ Test the admin Site Admin view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/siteadminview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Site - Site Admin - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/siteadminview/?sort=1" '
                'title="Sort by Username">Username</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (4)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_sitetositeview(self, login_func):
        """ Test the admin Site To Site view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/sitetositeview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Site - Site To Site - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/sitetositeview/?sort=2" '
                'title="Sort by Username">Username</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in output.data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_versionview(self, login_func):
        """ Test the admin Version view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/versionview/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Version - Admin'
                '</title>' in output.data)
            self.assertTrue(
                '<a href="/admin/archview/">Arch</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/categoryview/">Category</a>' in output.data)
            self.assertTrue(
                '<a href="/admin/versionview/?sort=1" '
                'title="Sort by Name">Name</a>' in output.data)
            self.assertTrue(
                '<a href="javascript:void(0)">List (6)</a>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAdminTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
