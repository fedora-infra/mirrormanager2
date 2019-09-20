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
import re
from mock import patch
import mirrormanager2.admin
import mirrormanager2.app
from mirrormanager2.lib import model
import tests


class FlaskUiAdminTest(tests.Modeltests):
    """ Flask tests. """

    def handle_flask_admin_urls(self, url):
        if url.endswith('/'):
            url = url[:-1]
        output = self.app.get(url + 'view/')
        if output.status_code == 404:
            output = self.app.get(url + '/')
        self.assertEqual(output.status_code, 200)
        return output

    def setUp(self):
        """ Set up the environnment, ran before every test. """
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

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<title>Home - Admin</title>' in data)
            self.assertFalse(
                '<a href="/admin/archview/">Arch</a>' in data)
            self.assertFalse(
                '<a href="/admin/categoryview/">Category</a>' in data)

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<title>Home - Admin</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_arch(self, login_func):
        """ Test the admin Arch view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/arch/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<title>Arch - Admin</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/\?sort=0" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (4)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_category(self, login_func):
        """ Test the admin Category view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/category/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<title>Category - Admin</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/\?sort=[02]" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (2)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_country(self, login_func):
        """ Test the admin Country view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/country/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Country - Country - Admin</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/country(view)?/\?sort=0" '
                'title="Sort by Code">Code</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (2)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_countrycontinentredirectview(self, login_func):
        """ Test the admin CountryContinentRedirect view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls(
                '/admin/countrycontinentredirect/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Country - Country Continent Redirect - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/countrycontinentredirect(view)?/\?sort=0" '
                'title="Sort by Country">Country</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_embargoedcountryview(self, login_func):
        """ Test the admin EmbargoedCountry view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/embargoedcountry/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Country - Embargoed Country - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/embargoedcountry(view)?/\?sort=0" '
                'title="Sort by Country Code">Country Code</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_directoryview(self, login_func):
        """ Test the admin Directory view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/directory/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Directory - Directory - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/directory(view)?/\?sort=0" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (9)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_directoryexclusivehostview(self, login_func):
        """ Test the admin DirectoryExclusiveHost view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls(
                '/admin/directoryexclusivehost/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Directory - Directory Exclusive Host - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertEqual(
                data.count('<th class="column-header">'), 3)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_filedetailview(self, login_func):
        """ Test the admin FileDetail view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/filedetail/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>File - File Detail - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/filedetail(view)?/\?sort=[01]" '
                'title="Sort by Filename">Filename</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_filedetailfilegroupview(self, login_func):
        """ Test the admin FileDetailFileGroup view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls(
                '/admin/filedetailfilegroup/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>File - File Detail File Group - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertEqual(
                data.count('<th class="column-header">'), 0)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_filegroupview(self, login_func):
        """ Test the admin FileGroup view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/filegroup/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>File - File Group - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/filegroup(view)?/\?sort=0" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostview(self, login_func):
        """ Test the admin Host view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/host/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/host(view)?/\?sort=[0-9]" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (4)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostaclipview(self, login_func):
        """ Test the admin Host Acl Ip view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostaclip/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Acl Ip - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/hostaclip(view)?/\?sort=[01]" '
                'title="Sort by Ip">Ip</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcategoryview(self, login_func):
        """ Test the admin Host Category view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostcategory/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Category - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/hostcategory(view)?/\?sort=[02]" '
                'title="Sort by Always Up2Date">Always Up2Date</a>',
                data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (4)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcategorydirview(self, login_func):
        """ Test the admin Host Category Dir view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostcategorydir/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Category Dir - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/hostcategorydir(view)?/\?sort=[02]" '
                'title="Sort by Path">Path</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (2)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcategoryurlview(self, login_func):
        """ Test the admin Host Category Url view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostcategoryurl/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Category Url - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/hostcategoryurl(view)?/\?sort=[01]" '
                'title="Sort by Url">Url</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (8)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcountryview(self, login_func):
        """ Test the admin Host Country view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostcountry/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Country - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertEqual(
                data.count('<th class="column-header">'), 2)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostcountryallowedview(self, login_func):
        """ Test the admin Host Country Allowed view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostcountryallowed/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Country Allowed - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/hostcountryallowed(view)?/\?sort=[01]" '
                'title="Sort by Country">Country</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostlocationview(self, login_func):
        """ Test the admin Host Location view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostlocation/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Location - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertEqual(
                data.count('<th class="column-header">'), 2)
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostnetblockview(self, login_func):
        """ Test the admin Host Netblock view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostnetblock/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Netblock - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/hostnetblock(view)?/\?sort=[02]" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hostpeerasnview(self, login_func):
        """ Test the admin Host Peer Asn view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hostpeerasn/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Peer Asn - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/hostpeerasn(view)?/\?sort=[02]" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_hoststatsview(self, login_func):
        """ Test the admin Host Stats view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/hoststats/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Host - Host Stats - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/hoststats(view)?/\?sort=[02]" '
                'title="Sort by Type">Type</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_locationview(self, login_func):
        """ Test the admin Location view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/location/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Location - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/location(view)?/\?sort=0" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_netblockcountryview(self, login_func):
        """ Test the admin Netblock Country view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/netblockcountry/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Netblock Country - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/netblockcountry(view)?/\?sort=0" '
                'title="Sort by Netblock">Netblock</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (1)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_productview(self, login_func):
        """ Test the admin Product view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/product/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Product - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/product(view)?/\?sort=0" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (2)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_repositoryview(self, login_func):
        """ Test the admin Repository view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/repository/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Repository - Repository - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/repository(view)?/\?sort=[0-4]" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (4)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_repositoryredirectview(self, login_func):
        """ Test the admin Repository Redirect view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/repositoryredirect/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Repository - Repository Redirect - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/repositoryredirect(view)?/\?sort=0" '
                'title="Sort by To Repo">To Repo</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_siteview(self, login_func):
        """ Test the admin Site view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/site/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Site - Site - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/site(view)?/\?sort=0" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (3)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_siteadminview(self, login_func):
        """ Test the admin Site Admin view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/siteadmin/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Site - Site Admin - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/siteadmin(view)?/\?sort=[01]" '
                'title="Sort by Username">Username</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (5)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_sitetositeview(self, login_func):
        """ Test the admin Site To Site view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/sitetosite/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Site - Site To Site - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/sitetosite(view)?/\?sort=[0-2]" '
                'title="Sort by Username">Username</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (0)</a>' in data)

    @patch('mirrormanager2.app.is_mirrormanager_admin')
    def test_admin_versionview(self, login_func):
        """ Test the admin Version view. """
        login_func.return_value = None

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.handle_flask_admin_urls('/admin/version/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Version - Admin'
                '</title>' in data)
            self.assertTrue(re.search(
                '<a href="/admin/arch(view)?/">Arch</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/category(view)?/">Category</a>', data))
            self.assertTrue(re.search(
                '<a href="/admin/version(view)?/\?sort=[01]" '
                'title="Sort by Name">Name</a>', data))
            self.assertTrue(
                '<a href="javascript:void(0)">List (6)</a>' in data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAdminTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
