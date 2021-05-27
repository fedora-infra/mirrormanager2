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
import mirrormanager2.admin
import mirrormanager2.app
from mirrormanager2.lib import model
import tests


class FlaskUiAppTest(tests.Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every test. """
        super(FlaskUiAppTest, self).setUp()

        skip = os.getenv('MM2_SKIP_NETWORK_TESTS', 0)
        self.network_tests = not bool(skip)
        if skip:
            raise unittest.SkipTest('Skipping FlaskUiAppTest tests')

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
        tests.create_hostcountry(self.session)
        tests.create_hostpeerasn(self.session)
        tests.create_hostnetblock(self.session)
        tests.create_categorydirectory(self.session)
        tests.create_version(self.session)
        tests.create_repository(self.session)
        tests.create_repositoryredirect(self.session)

    def test_index(self):
        """ Test the index endpoint. """

        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        self.assertTrue('<title>Home - MirrorManager</title>' in data)
        self.assertTrue(
            '<a class="nav-link" href="/mirrors">Mirrors</a>' in data)
        self.assertTrue(
            'href="/login?next=http://localhost/">Login</a>'
            in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Home - MirrorManager</title>' in data)
            self.assertTrue(
                '<a class="nav-link" href="/mirrors">Mirrors</a>'
                in data)
            self.assertFalse(
                'href="/login?next=http://127.0.0.1:5000/">login/a>'
                in data)
            self.assertTrue(
                '<a class="dropdown-item" href="/site/mine">My Sites</a>'
                in data)
            self.assertTrue(
                'href="/logout?next=http://localhost/">Log Out</a>'
                in data)

    def test_list_mirrors(self):
        """ Test the list_mirrors endpoint. """
        output = self.app.get('/mirrors')
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        self.assertTrue(
            '<title>Mirrors - MirrorManager</title>' in data)
        self.assertTrue(
            '<h2>Public active mirrors</h2>' in data)
        self.assertTrue(
            'We have currently 2 active mirrors' in data)

        for i in [27, 26, 25]:
            output = self.app.get('/mirrors/Fedora/%s' % i)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Mirrors - MirrorManager</title>' in data)
            self.assertTrue(
                '<a class="nav-link" href="/mirrors">Mirrors</a>'
                in data)
            self.assertTrue(
                'We have currently 2 active mirrors' in data)

            output = self.app.get('/mirrors/Fedora Linux/%s/x86_64' % i)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Mirrors - MirrorManager</title>' in data)
            self.assertTrue(
                '<a class="nav-link" href="/mirrors">Mirrors</a>'
                in data)
            self.assertTrue(
                'We have currently 2 active mirrors' in data)

            output = self.app.get('/mirrors/Fedora Linux/20/i386')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Mirrors - MirrorManager</title>' in data)
            self.assertTrue(
                '<a class="nav-link" href="/mirrors">Mirrors</a>'
                in data)
            self.assertTrue(
                'There are currently no active mirrors registered.'
                in data)

    def test_mysite(self):
        """ Test the mysite endpoint. """
        output = self.app.get('/site/mine')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/site/mine', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/site/mine')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                'You have currently 1 sites listed' in data)

    def test_all_sites(self):
        """ Test the all_sites endpoint. """
        output = self.app.get('/admin/all_sites')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/admin/all_sites', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/all_sites')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/admin/all_sites', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="error">You are not an admin</li>' in data)
            self.assertTrue(
                '<title>Home - MirrorManager</title>' in data)
            self.assertTrue(
                '<a class="nav-link" href="/mirrors">Mirrors</a>'
                in data)

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/admin/all_sites')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>Home - MirrorManager</title>' in data)
            self.assertTrue(
                '<a class="nav-link" href="/mirrors">Mirrors</a>'
                in data)
            self.assertTrue(
                '<h2>Admin - List all sites</h2>' in data)
            self.assertTrue(
                'You have currently 3 sites listed' in data)

    def test_site_new(self):
        """ Test the site_new endpoint. """
        output = self.app.get('/site/new')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/site/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/site/new')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>New Site - MirrorManager</title>'
                in data)
            self.assertTrue(
                '<h2>Export Compliance</h2>' in data)
            self.assertTrue(
                'td><label for="name">Site name</label></td>'
                in data)
            self.assertTrue(
                '<a class="nav-link" href="/mirrors">Mirrors</a>'
                in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {
                'name': 'pingoured.fr',
                'password': 'foobar',
                'org_url': 'http://pingoured.fr',
                'admin_active': True,
                'user_active': True,
            }

            # Check CSRF protection

            output = self.app.post('/site/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>New Site - MirrorManager</title>' in data)
            self.assertTrue(
                '<h2>Export Compliance</h2>' in data)
            self.assertTrue(
                'td><label for="name">Site name</label></td>' in data)
            self.assertTrue(
                '<a class="nav-link" href="/mirrors">Mirrors</a>'
                in data)

            # Create the new site

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/site/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Site added</li>' in data)
            self.assertTrue(
                '<li class="message">pingou added as an admin</li>'
                in data)
            self.assertTrue(
                '<h2>Fedora Public Active Mirrors</h2>' in data)

            output = self.app.get('/site/mine')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                'You have currently 2 sites listed' in data)

    def test_site_view(self):
        """ Test the site_view endpoint. """
        output = self.app.get('/site/2')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/site/2', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/site/5')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Site not found</p>' in data)

            # Test if accessing other sites is not allowed
            output = self.app.get('/site/1')
            self.assertEqual(output.status_code, 403)

            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertTrue('mirror2.localhost</a> <br />' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Incomplete input
            post_data = {
                'name': 'test-mirror2.1',
            }

            output = self.app.post('/site/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertEqual(data.count('field is required.'), 2)

            post_data = {
                'name': 'test-mirror2.1',
                'password': 'test_password2',
                'org_url': 'http://getfedora.org',
                'admin_active': True,
                'user_active': True,
                'downstream_comments': 'Mirror available over HTTP.',
            }

            # Check CSRF protection

            output = self.app.post('/site/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)

            # Update site

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/site/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Fedora Public Active Mirrors</h2>' in data)
            self.assertTrue(
                '<li class="message">Site Updated</li>' in data)

            # Check after the edit
            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2.1</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertTrue('mirror2.localhost</a> <br />' in data)

    def test_host_new(self):
        """ Test the host_new endpoint. """
        output = self.app.get('/host/2/new')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/host/2/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            # Invalid site identifier
            output = self.app.get('/host/5/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Site not found</p>' in data)

            # Check before adding the host
            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertTrue('mirror2.localhost</a> <br />' in data)
            self.assertFalse('pingoured.fr</a> <br />' in data)

            # Test host_new
            output = self.app.get('/host/2/new')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>New Host - MirrorManager</title>' in data)
            self.assertTrue(
                '<h2>Create new host</h2>' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {
                'name': 'pingoured.fr',
                'admin_active': True,
                'user_active': True,
                'country': 'FR',
                'bandwidth_int': 100,
                'asn_clients': True,
                'max_connections': 3,
            }

            # Check CSRF protection

            output = self.app.post('/host/2/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>New Host - MirrorManager</title>' in data)
            self.assertTrue(
                '<h2>Create new host</h2>' in data)

            # Create Host

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/host/2/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host added</li>' in data)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertTrue('mirror2.localhost</a> <br />' in data)
            self.assertTrue('pingoured.fr</a> <br />' in data)

            # Try creating the same host -- will fail
            output = self.app.post('/host/2/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Could not create the new host</li>'
                in data)

    def test_siteadmin_new(self):
        """ Test the siteadmin_new endpoint. """
        output = self.app.get('/site/2/admin/new')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/site/2/admin/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            # Invalid site identifier
            output = self.app.get('/site/5/admin/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Site not found</p>' in data)

            # Check before adding the host
            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertFalse(
                'action="/site/2/admin/5/delete">' in data)
            self.assertFalse('skvidal' in data)

            # Test host_new
            output = self.app.get('/site/2/admin/new')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>New Site Admin - MirrorManager</title>' in data)
            self.assertTrue(
                '<h2>Add Site admin to site: test-mirror2</h2>'
                in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {
                'username': 'skvidal',
            }

            # Check CSRF protection

            output = self.app.post('/site/2/admin/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<title>New Site Admin - MirrorManager</title>' in data)
            self.assertTrue(
                '<h2>Add Site admin to site: test-mirror2</h2>'
                in data)

            # Create Admin

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/site/2/admin/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Site Admin added</li>' in data)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertTrue('action="/site/2/admin/3/delete">' in data)
            self.assertTrue('skvidal' in data)

    def test_siteadmin_delete(self):
        """ Test the siteadmin_delete endpoint. """
        output = self.app.post('/site/2/admin/3/delete')
        self.assertEqual(output.status_code, 302)

        output = self.app.post('/site/2/admin/3/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertTrue(
                'action="/site/2/admin/3/delete">' in data)
            self.assertEqual(data.count('ralph'), 1)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {}

            # Check CSRF protection

            output = self.app.post('/site/2/admin/3/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertTrue(
                'action="/site/2/admin/3/delete">' in data)
            self.assertEqual(data.count('ralph'), 1)

            # Delete Site Admin

            post_data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post('/site/5/admin/3/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Site not found</p>' in data)

            # Invalid site admin identifier
            output = self.app.post('/site/2/admin/9/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Site Admin not found</p>' in data)

            # Valid site admin but not for this site
            output = self.app.post('/site/2/admin/1/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<p>Site Admin not related to this Site</p>' in data)

            # Delete Site Admin
            output = self.app.post('/site/2/admin/3/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in data)
            self.assertTrue('Created by: kevin' in data)
            self.assertFalse(
                'action="/site/2/admin/3/delete">' in data)
            self.assertEqual(data.count('ralph'), 0)

            # Trying to delete the only admin
            output = self.app.post('/site/2/admin/4/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="error">There is only one admin set, you cannot '
                'delete it.</li>' in data)

    def test_host_view(self):
        """ Test the host_view endpoint. """
        output = self.app.get('/host/5')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/host/5', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            # Test if accessing other hosts is not allowed
            output = self.app.get('/host/3')
            self.assertEqual(output.status_code, 403)

            output = self.app.get('/host/2')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Host mirror2.localhost' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Incomplete input
            post_data = {
                'name': 'private.localhost.1',
            }

            output = self.app.post('/host/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Host mirror2.localhost' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertEqual(data.count('field is required.'), 3)

            post_data = {
                'name': 'private.localhost.1',
                'admin_active': True,
                'user_active': True,
                'country': 'NL',
                'bandwidth_int': 100,
                'asn_clients': True,
                'max_connections': 10,
                'comment': 'My own private mirror',
            }

            # Check CSRF protection

            output = self.app.post('/host/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Host mirror2.localhost' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)

            # Update site

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/host/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Host private.localhost.1' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)

    def test_host_netblock_new(self):
        """ Test the host_netblock_new endpoint. """
        output = self.app.get('/host/3/netblock/new')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/host/3/netblock/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.AnotherFakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/netblock/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            output = self.app.get('/host/3/netblock/new')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host netblock</h2>' in data)
            self.assertTrue('Back to <a href="/host/3">' in data)
            self.assertTrue(
                '<title>New Host netblock - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/3/host_netblock/2/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {
                'netblock': '192.168.0.0/24',
                'name': 'home network',
            }

            # Check CSRF protection

            output = self.app.post('/host/3/netblock/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host netblock</h2>' in data)
            self.assertTrue('Back to <a href="/host/3">' in data)
            self.assertTrue(
                '<title>New Host netblock - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/3/host_netblock/1/delete">' in data)

            # Update site

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/host/3/netblock/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host netblock added</li>' in data)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/3/host_netblock/2/delete">' in data)

    def test_host_netblock_delete(self):
        """ Test the host_netblock_delete endpoint. """
        output = self.app.post('/host/3/host_netblock/1/delete')
        self.assertEqual(output.status_code, 302)

        output = self.app.post(
            '/host/3/host_netblock/1/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.AnotherFakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/host/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/3/host_netblock/1/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {}

            # Check CSRF protection

            output = self.app.post(
                '/host/3/host_netblock/1/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/3/host_netblock/1/delete">' in data)

            # Delete Site Admin

            post_data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post(
                '/host/5/host_netblock/1/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            # Invalid site admin identifier
            output = self.app.post(
                '/host/3/host_netblock/2/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host netblock not found</p>' in data)

            # Delete Site Admin
            output = self.app.post(
                '/host/3/host_netblock/1/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host netblock deleted</li>'
                in data)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertFalse(
                'action="/host/3/host_netblock/1/delete">' in data)

    def test_host_asn_new(self):
        """ Test the host_asn_new endpoint. """
        output = self.app.get('/host/3/asn/new')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/host/3/asn/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/asn/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            output = self.app.get('/host/3/asn/new')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host Peer ASNs</h2>' in data)
            self.assertTrue('Back to <a href="/host/3">' in data)
            self.assertTrue(
                '<title>New Host Peer ASN - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/3/host_asn/2/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {
                'asn': '192168',
                'name': 'ASN pingoured',
            }

            # Check CSRF protection

            output = self.app.post('/host/3/asn/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host Peer ASNs</h2>' in data)
            self.assertTrue('Back to <a href="/host/3">' in data)
            self.assertTrue(
                '<title>New Host Peer ASN - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/3/host_asn/2/delete">' in data)

            # Update site

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/host/3/asn/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host Peer ASN added</li>' in data)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/3/host_asn/2/delete">' in data)

    def test_host_asn_delete(self):
        """ Test the host_asn_delete endpoint. """
        output = self.app.post('/host/3/host_asn/1/delete')
        self.assertEqual(output.status_code, 302)

        output = self.app.post(
            '/host/3/host_asn/1/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUserAdmin()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/host/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/3/host_asn/1/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {}

            # Check CSRF protection

            output = self.app.post('/host/3/host_asn/1/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/3/host_asn/1/delete">' in data)

            # Delete Host ASN

            post_data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post('/host/5/host_asn/1/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            # Invalid Host ASN identifier
            output = self.app.post('/host/3/host_asn/2/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host Peer ASN not found</p>' in data)

            # Delete Host ASN
            output = self.app.post(
                '/host/3/host_asn/1/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host Peer ASN deleted</li>'
                in data)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertFalse(
                'action="/host/3/host_asn/1/delete">' in data)

    def test_host_country_new(self):
        """ Test the host_country_new endpoint. """
        output = self.app.get('/host/5/country/new')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/host/5/country/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.AnotherFakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/country/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            output = self.app.get('/host/3/country/new')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host country allowed</h2>' in data)
            self.assertTrue('Back to <a href="/host/3">' in data)
            self.assertTrue(
                '<title>New Host Country - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/3/host_country/3/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {
                'country': 'GB',
            }

            # Check CSRF protection

            output = self.app.post('/host/3/country/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host country allowed</h2>' in data)
            self.assertTrue('Back to <a href="/host/3">' in data)
            self.assertTrue(
                '<title>New Host Country - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/3/host_country/3/delete">' in data)

            # Invalid Country code

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/host/3/country/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Invalid country code</li>'
                in data)
            self.assertTrue(
                '<h2>Add host country allowed</h2>' in data)
            self.assertTrue('Back to <a href="/host/3">' in data)
            self.assertTrue(
                '<title>New Host Country - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/3/host_country/3/delete">' in data)

            # Create Country

            post_data['country'] = 'FR'

            output = self.app.post('/host/3/country/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host Country added</li>' in data)
            self.assertTrue('<h2>Host private.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/3/host_country/3/delete">' in data)

    def test_host_country_delete(self):
        """ Test the host_country_delete endpoint. """
        output = self.app.post('/host/1/host_country/1/delete')
        self.assertEqual(output.status_code, 302)

        output = self.app.post(
            '/host/1/host_country/2/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.AnotherFakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/host/1')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host mirror.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/1/host_country/1/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {}

            # Check CSRF protection

            output = self.app.post('/host/1/host_country/1/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host mirror.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/1/host_country/1/delete">' in data)

            # Delete Host Country

            post_data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post('/host/5/host_country/1/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            # Invalid Host Country identifier
            output = self.app.post('/host/1/host_country/5/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host Country not found</p>' in data)

            # Delete Host Country
            output = self.app.post(
                '/host/1/host_country/1/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host Country deleted</li>'
                in data)
            self.assertTrue('<h2>Host mirror.localhost' in data)
            self.assertTrue('Back to <a href="/site/1">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertFalse(
                'action="/host/1/host_country/1/delete">' in data)

    def test_host_category_new(self):
        """ Test the host_category_new endpoint. """
        output = self.app.get('/host/5/category/new')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/host/5/category/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/category/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            output = self.app.get('/host/2/category/new')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host category</h2>' in data)
            self.assertTrue('Back to <a href="/host/2">' in data)
            self.assertTrue(
                '<title>New Host Category - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/2/category/1/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {
                'category_id': 'Fedora Linux',
            }

            # Invalid input

            output = self.app.post('/host/2/category/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host category</h2>' in data)
            self.assertTrue('Back to <a href="/host/2">' in data)
            self.assertTrue(
                '<title>New Host Category - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/2/category/1/delete">' in data)
            self.assertTrue(
                'Invalid Choice: could not coerce<br />Not a valid choice'
                in data)

            # Check CSRF protection

            output = self.app.post('/host/2/category/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host category</h2>' in data)
            self.assertTrue('Back to <a href="/host/2">' in data)
            self.assertTrue(
                '<title>New Host Category - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/2/category/1/delete">' in data)

            # Delete before adding

            post_data['csrf_token'] = csrf_token

            output = self.app.post(
                '/host/2/category/4/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)

            # Add Category

            post_data['csrf_token'] = csrf_token
            post_data['category_id'] = '2'

            output = self.app.post('/host/2/category/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host Category added</li>' in data)
            self.assertTrue('<h2>Host category</h2>' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in data)

            # Try adding the same Category -- fails

            output = self.app.post('/host/2/category/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Could not add Category to the host</li>'
                in data)
            self.assertTrue(
                '<h2>Add host category</h2>' in data)
            self.assertTrue('Back to <a href="/host/2">' in data)
            self.assertTrue(
                '<title>New Host Category - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/2/category/1/delete">' in data)

            # Check host after adding the category
            output = self.app.get('/host/2')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host mirror2.localhost' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/2/category/4/delete">' in data)

    def test_host_category_delete(self):
        """ Test the host_category_delete endpoint. """
        output = self.app.post('/host/1/category/1/delete')
        self.assertEqual(output.status_code, 302)

        output = self.app.post(
            '/host/1/category/1/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before deleting the category
            output = self.app.get('/host/2')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host mirror2.localhost' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/2/category/3/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {}

            # Check CSRF protection

            output = self.app.post('/host/2/category/1/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host mirror2.localhost' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/2/category/3/delete">' in data)

            # Delete Host Category

            post_data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post('/host/5/category/1/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            # Invalid Host Category identifier
            output = self.app.post('/host/2/category/50/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host/Category not found</p>' in data)

            # Invalid Host/Category association
            output = self.app.post('/host/2/category/1/delete', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<p>Category not associated with this host</p>'
                in data)

            # Delete Host Category
            output = self.app.post(
                '/host/2/category/3/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host Category deleted</li>'
                in data)
            self.assertTrue('<h2>Host mirror2.localhost' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in data)
            self.assertFalse(
                'action="/host/2/category/1/delete">' in data)

    def test_host_category_url_new(self):
        """ Test the host_category_url_new endpoint. """
        output = self.app.get('/host/1/category/1/url/new')
        self.assertEqual(output.status_code, 302)

        output = self.app.get(
            '/host/1/category/1/url/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/category/1/url/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            output = self.app.get('/host/2/category/50/url/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host/Category not found</p>' in data)

            output = self.app.get('/host/2/category/1/url/new')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<p>Category not associated with this host</p>'
                in data)

            output = self.app.get('/host/2/category/3/url/new')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host category URL</h2>' in data)
            self.assertTrue(
                'test-mirror2</a> / <a href="/host/2">' in data)
            self.assertTrue(
                '<title>New Host Category URL - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/2/category/3/url/5/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {
                'url': 'http://pingoured.fr/pub/Fedora/',
            }

            # Check CSRF protection

            output = self.app.post('/host/2/category/3/url/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Add host category URL</h2>' in data)
            self.assertTrue(
                'test-mirror2</a> / <a href="/host/2">' in data)
            self.assertTrue(
                '<title>New Host Category URL - MirrorManager</title>'
                in data)
            self.assertFalse(
                'action="/host/2/category/3/url/5/delete">' in data)

            # Add Host Category URL

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/host/2/category/3/url/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host Category URL added</li>'
                in data)
            self.assertTrue('<h2>Host category</h2>' in data)
            self.assertTrue(
                'test-mirror2</a> / <a href="/host/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/2/category/3/url/9/delete">' in data)

            # Try adding the same Host Category URL -- fails

            post_data['csrf_token'] = csrf_token

            output = self.app.post('/host/2/category/3/url/new', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                'class="message">Could not add Category URL to the host</li>'
                in data)
            self.assertTrue('<h2>Host category</h2>' in data)
            self.assertTrue(
                'test-mirror2</a> / <a href="/host/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/2/category/3/url/9/delete">' in data)

    def test_host_category_url_delete(self):
        """ Test the host_category_url_delete endpoint. """
        output = self.app.post('/host/1/category/1/url/3/delete')
        self.assertEqual(output.status_code, 302)

        output = self.app.post(
            '/host/1/category/1/url/3/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before deleting the category URL
            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host category</h2>' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/2/category/3/url/5/delete">' in data)

            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            post_data = {}

            # Check CSRF protection

            output = self.app.post(
                '/host/2/category/3/url/5/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue('<h2>Host category</h2>' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in data)
            self.assertTrue(
                'action="/host/2/category/3/url/5/delete">' in data)

            # Delete Host Category URL

            post_data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post(
                '/host/5/category/5/url/5/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            # Invalid Host Category identifier
            output = self.app.post(
                '/host/2/category/50/url/5/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host/Category not found</p>' in data)

            # Invalid Host/Category association
            output = self.app.post(
                '/host/2/category/3/url/4/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<p>Category URL not associated with this host</p>'
                in data)

            # Invalid Category/URL
            output = self.app.post(
                '/host/2/category/3/url/50/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<p>Host category URL not found</p>'
                in data)

            # Invalid Category/URL association
            output = self.app.post(
                '/host/2/category/2/url/4/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<p>Category not associated with this host</p>'
                in data)

            # Delete Host Category URL
            output = self.app.post(
                '/host/2/category/3/url/5/delete', data=post_data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">Host category URL deleted</li>'
                in data)
            self.assertTrue('<h2>Host category</h2>' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in data)
            self.assertFalse(
                'action="/host/2/category/3/url/5/delete">' in data)

    def test_host_category(self):
        """ Test the host_category endpoint. """

        output = self.app.post('/host/2/category/5')
        self.assertEqual(output.status_code, 302)

        output = self.app.post('/host/2/category/5', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/category/5')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            output = self.app.get('/host/2/category/50')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host/Category not found</p>' in data)

            output = self.app.get('/host/2/category/2')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<p>Category not associated with this host</p>'
                in data)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h3>Up-to-Date Directories this host carries</h3>'
                in data)

    def test_auth_logout(self):
        """ Test the auth_logout endpoint. """
        output = self.app.get('/logout')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        self.assertTrue(
            '<h2>Fedora Public Active Mirrors</h2>' in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/logout')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/logout', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="message">You are no longer logged-in</li>'
                in data)
            self.assertTrue(
                '<h2>Fedora Public Active Mirrors</h2>' in data)

    def test_toggle_private_flag_host(self):
        """
        Test that the toggling of the private flag in the host
        deletes all host category directories.
        """
        output = self.app.get('/host/2/category/3')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/host/2/category/3', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/category/3')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                'pub/fedora/linux/releases/27' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in data)

            output = self.app.get('/host/2')
            data = output.get_data(as_text=True)
            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Toggle private flag -> private: True
            post_data = {
                'name': 'mirror2.localhost',
                'admin_active': True,
                'private': True,
                'user_active': True,
                'country': 'FR',
                'bandwidth_int': 100,
                'asn_clients': True,
                'max_connections': 10,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/host/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            # Make sure the host_category_directory is gone
            self.assertFalse(
                'pub/fedora/linux/releases/27' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in data)
            # more test data
            tests.create_hostcategorydir_one_more(self.session)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                'pub/fedora/linux/updates/testing/26/x86_64' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in data)

            # Toggle private flag -> private: False (or rather None)
            post_data = {
                'name': 'mirror2.localhost',
                'admin_active': True,
                'private': None,
                'user_active': True,
                'country': 'FR',
                'bandwidth_int': 100,
                'asn_clients': True,
                'max_connections': 10,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/host/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            # Make sure the host_category_directory is gone
            self.assertFalse(
                'pub/fedora/linux/updates/testing/26/x86_64' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in data)


    def test_toggle_private_flag_site(self):
        """
        Test that the toggling of the private flag in the site
        deletes all host category directories.
        """
        output = self.app.get('/host/2/category/3')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/host/2/category/3', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        data = output.get_data(as_text=True)
        if self.network_tests:
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/category/3')
            self.assertEqual(output.status_code, 404)
            data = output.get_data(as_text=True)
            self.assertTrue('<p>Host not found</p>' in data)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                'pub/fedora/linux/releases/27' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in data)

            output = self.app.get('/host/2')
            data = output.get_data(as_text=True)
            csrf_token = data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # more test data
            tests.create_hostcategorydir_even_more(self.session)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                'pub/fedora/linux/updates/testing/27/x86_64' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in data)

            post_data = {
                'name': 'test-mirror2.1',
                'password': 'test_password2',
                'org_url': 'http://getfedora.org',
                'admin_active': True,
                'user_active': True,
                'private': True,
                'downstream_comments': 'Mirror available over HTTP.',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/site/2', data=post_data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            self.assertTrue(
                '<h2>Fedora Public Active Mirrors</h2>' in data)
            self.assertTrue(
                '<li class="message">Site Updated</li>' in data)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            data = output.get_data(as_text=True)
            # Make sure the host_category_directory is gone
            self.assertFalse(
                'pub/fedora/linux/updates/testing/27/x86_64' in data)
            self.assertTrue('Back to <a href="/site/2">' in data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAppTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
