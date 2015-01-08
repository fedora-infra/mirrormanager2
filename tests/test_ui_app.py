# -*- coding: utf-8 -*-

'''
mirrormanager2 tests for the Flask application.
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


class FlaskUiAppTest(tests.Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskUiAppTest, self).setUp()

        mirrormanager2.app.APP.config['TESTING'] = True
        mirrormanager2.app.SESSION = self.session
        mirrormanager2.app.ADMIN.SESSION = self.session
        mirrormanager2.app.APP.SESSION = self.session
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

    def test_index(self):
        """ Test the index endpoint. """

        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title>Home - MirrorManager</title>' in output.data)
        self.assertTrue('<li id="homeTab">' in output.data)
        self.assertTrue('<li id="mirrorsTab">' in output.data)
        self.assertTrue(
            '<a href="/login?next=http://localhost/">login</a>'
            in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Home - MirrorManager</title>' in output.data)
            self.assertTrue('<li id="homeTab">' in output.data)
            self.assertTrue('<li id="mirrorsTab">' in output.data)
            self.assertFalse(
                '<a href="/login?next=http://127.0.0.1:5000/">login/a>'
                in output.data)
            self.assertTrue(
                '<span class="text">logged in as </span>' in output.data)
            self.assertTrue(
                '<a href="/logout?next=http://localhost/">log out</a>'
                in output.data)

    def test_list_mirrors(self):
        """ Test the list_mirrors endpoint. """
        output = self.app.get('/mirrors')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title>Home - MirrorManager</title>' in output.data)
        self.assertTrue('<li id="homeTab">' in output.data)
        self.assertTrue('<li id="mirrorsTab">' in output.data)
        self.assertTrue('We have currently 1 active mirrors' in output.data)

        for i in [21, 20, 19]:
            output = self.app.get('/mirrors/Fedora/%s' % i)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - MirrorManager</title>' in output.data)
            self.assertTrue('<li id="homeTab">' in output.data)
            self.assertTrue('<li id="mirrorsTab">' in output.data)
            self.assertTrue(
                'We have currently 1 active mirrors' in output.data)

            output = self.app.get('/mirrors/Fedora Linux/%s/x86_64' % i)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - MirrorManager</title>' in output.data)
            self.assertTrue('<li id="homeTab">' in output.data)
            self.assertTrue('<li id="mirrorsTab">' in output.data)
            self.assertTrue(
                'We have currently 1 active mirrors' in output.data)

            output = self.app.get('/mirrors/Fedora Linux/20/i386')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - MirrorManager</title>' in output.data)
            self.assertTrue('<li id="homeTab">' in output.data)
            self.assertTrue('<li id="mirrorsTab">' in output.data)
            self.assertTrue(
                'There are currently no active mirrors registered.'
                in output.data)

    def test_mysite(self):
        """ Test the mysite endpoint. """
        output = self.app.get('/site/mine')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/site/mine', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/site/mine')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'You have currently 1 sites listed' in output.data)

    def test_all_sites(self):
        """ Test the all_sites endpoint. """
        output = self.app.get('/admin/all_sites')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/admin/all_sites', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/all_sites')
            self.assertEqual(output.status_code, 302)
            output = self.app.get('/admin/all_sites', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">You are not an admin</li>' in output.data)
            self.assertTrue(
                '<title>Home - MirrorManager</title>' in output.data)
            self.assertTrue('<li id="homeTab">' in output.data)
            self.assertTrue('<li id="mirrorsTab">' in output.data)

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/all_sites')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - MirrorManager</title>' in output.data)
            self.assertTrue('<li id="homeTab">' in output.data)
            self.assertTrue('<li id="mirrorsTab">' in output.data)
            self.assertTrue(
                '<h2>Admin - List all sites</h2>' in output.data)
            self.assertTrue(
                'You have currently 3 sites listed' in output.data)

    def test_site_new(self):
        """ Test the site_new endpoint. """
        output = self.app.get('/site/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/site/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/site/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>New Site - MirrorManager</title>' in output.data)
            self.assertTrue(
                '<h2>Export Compliance</h2>' in output.data)
            self.assertTrue(
                'td><label for="name">Site name</label></td>' in output.data)
            self.assertTrue('<li id="homeTab">' in output.data)
            self.assertTrue('<li id="mirrorsTab">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'name': 'pingoured.fr',
                'password': 'foobar',
                'org_url': 'http://pingoured.fr',
                'admin_active': True,
                'user_active': True,
            }

            # Check CSRF protection

            output = self.app.post('/site/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>New Site - MirrorManager</title>' in output.data)
            self.assertTrue(
                '<h2>Export Compliance</h2>' in output.data)
            self.assertTrue(
                'td><label for="name">Site name</label></td>' in output.data)
            self.assertTrue('<li id="homeTab">' in output.data)
            self.assertTrue('<li id="mirrorsTab">' in output.data)

            # Create the new site

            data['csrf_token'] = csrf_token

            output = self.app.post('/site/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Site added</li>' in output.data)
            self.assertTrue(
                '<li class="message">pingou added as an admin</li>'
                in output.data)
            self.assertTrue(
                '<h2>Fedora Public Active Mirrors</h2>' in output.data)

            output = self.app.get('/site/mine')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'You have currently 2 sites listed' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAppTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
