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
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategoryurl(self.session)
        tests.create_categorydirectory(self.session)

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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAdminTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
