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

    def test_site_view(self):
        """ Test the site_view endpoint. """
        output = self.app.get('/site/2')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/site/2', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/site/5')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Site not found</p>' in output.data)

            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertTrue('mirror2.localhost</a> <br />' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Incomplete input
            data = {
                'name': 'test-mirror2.1',
            }

            output = self.app.post('/site/2', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertEqual(output.data.count('field is required.'), 2)

            data = {
                'name': 'test-mirror2.1',
                'password': 'test_password2',
                'org_url': 'http://getfedora.org',
                'admin_active': True,
                'user_active': True,
                'downstream_comments': 'Mirror available over HTTP.',
            }

            # Check CSRF protection

            output = self.app.post('/site/2', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)

            # Update site

            data['csrf_token'] = csrf_token

            output = self.app.post('/site/2', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Fedora Public Active Mirrors</h2>' in output.data)
            self.assertTrue(
                '<li class="message">Site Updated</li>' in output.data)

            # Check after the edit
            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2.1</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertTrue('mirror2.localhost</a> <br />' in output.data)

    def test_host_new(self):
        """ Test the host_new endpoint. """
        output = self.app.get('/host/2/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/host/2/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            # Invalid site identifier
            output = self.app.get('/host/5/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Site not found</p>' in output.data)

            # Check before adding the host
            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertTrue('mirror2.localhost</a> <br />' in output.data)
            self.assertFalse('pingoured.fr</a> <br />' in output.data)

            # Test host_new
            output = self.app.get('/host/2/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>New Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                '<h2>Create new host</h2>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'name': 'pingoured.fr',
                'admin_active': True,
                'user_active': True,
                'country': 'FR',
                'bandwidth_int': 100,
                'asn_clients': True,
                'max_connections': 3,
            }

            # Check CSRF protection

            output = self.app.post('/host/2/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>New Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                '<h2>Create new host</h2>' in output.data)

            # Create Host

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/2/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host added</li>' in output.data)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertTrue('mirror2.localhost</a> <br />' in output.data)
            self.assertTrue('pingoured.fr</a> <br />' in output.data)

            # Try creating the same host -- will fail
            output = self.app.post('/host/2/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Could not create the new host</li>'
                in output.data)

    def test_siteadmin_new(self):
        """ Test the siteadmin_new endpoint. """
        output = self.app.get('/site/2/admin/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/site/2/admin/new', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            # Invalid site identifier
            output = self.app.get('/site/5/admin/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Site not found</p>' in output.data)

            # Check before adding the host
            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertFalse(
                'action="/site/2/admin/5/delete">' in output.data)
            self.assertFalse('skvidal' in output.data)

            # Test host_new
            output = self.app.get('/site/2/admin/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>New Site Admin - MirrorManager</title>' in output.data)
            self.assertTrue(
                '<h2>Add Site admin to site: test-mirror2</h2>'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'username': 'skvidal',
            }

            # Check CSRF protection

            output = self.app.post('/site/2/admin/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>New Site Admin - MirrorManager</title>' in output.data)
            self.assertTrue(
                '<h2>Add Site admin to site: test-mirror2</h2>'
                in output.data)

            # Create Admin

            data['csrf_token'] = csrf_token

            output = self.app.post('/site/2/admin/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Site Admin added</li>' in output.data)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertTrue('action="/site/2/admin/3/delete">' in output.data)
            self.assertTrue('skvidal' in output.data)

    def test_siteadmin_delete(self):
        """ Test the siteadmin_delete endpoint. """
        output = self.app.post('/site/2/admin/3/delete')
        self.assertEqual(output.status_code, 302)
        output = self.app.post('/site/2/admin/3/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/site/2')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertTrue(
                'action="/site/2/admin/3/delete">' in output.data)
            self.assertEqual(output.data.count('ralph'), 1)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {}

            # Check CSRF protection

            output = self.app.post('/site/2/admin/3/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertTrue(
                'action="/site/2/admin/3/delete">' in output.data)
            self.assertEqual(output.data.count('ralph'), 1)

            # Delete Site Admin

            data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post('/site/5/admin/3/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Site not found</p>' in output.data)

            # Invalid site admin identifier
            output = self.app.post('/site/2/admin/9/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Site Admin not found</p>' in output.data)

            # Valid site admin but not for this site
            output = self.app.post('/site/2/admin/1/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue(
                '<p>Site Admin not related to this Site</p>' in output.data)

            # Trying to delete the only admin
            output = self.app.post('/site/3/admin/5/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="error">There is only one admin set, you cannot '
                'delete it.</li>' in output.data)

            # Delete Site Admin
            output = self.app.post('/site/2/admin/3/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Information site: test-mirror2</h2>' in output.data)
            self.assertTrue('Created by: kevin' in output.data)
            self.assertFalse(
                'action="/site/2/admin/3/delete">' in output.data)
            self.assertEqual(output.data.count('ralph'), 0)

    def test_host_view(self):
        """ Test the host_view endpoint. """
        output = self.app.get('/host/5')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/host/5', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            output = self.app.get('/host/3')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Incomplete input
            data = {
                'name': 'private.localhost.1',
            }

            output = self.app.post('/host/3', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertEqual(output.data.count('field is required.'), 3)

            data = {
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

            output = self.app.post('/host/3', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)

            # Update site

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/3', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Host private.localhost.1</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)

    def test_host_acl_ip_new(self):
        """ Test the host_acl_ip_new endpoint. """
        output = self.app.get('/host/5/host_acl_ip/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/host/5/host_acl_ip/new', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/host_acl_ip/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            output = self.app.get('/host/3/host_acl_ip/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host ACL IP</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host ACL IP - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_acl_ip/1/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'ip': '127.0.0.1',
            }

            # Check CSRF protection

            output = self.app.post('/host/3/host_acl_ip/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host ACL IP</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host ACL IP - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_acl_ip/1/delete">' in output.data)

            # Update site

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/3/host_acl_ip/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host ACL IP added</li>' in output.data)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_acl_ip/1/delete">' in output.data)

            # Error adding this IP again
            output = self.app.post('/host/3/host_acl_ip/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Could not add ACL IP to the host</li>'
                in output.data)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_acl_ip/1/delete">' in output.data)

    def test_host_acl_ip_delete(self):
        """ Test the host_acl_ip_delete endpoint. """
        # Create an Host ACL IP to delete
        self.test_host_acl_ip_new()

        output = self.app.post('/host/3/host_acl_ip/1/delete')
        self.assertEqual(output.status_code, 302)
        output = self.app.post(
            '/host/3/host_acl_ip/1/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/host/3')
            self.assertEqual(output.status_code, 200)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_acl_ip/1/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {}

            # Check CSRF protection

            output = self.app.post(
                '/host/3/host_acl_ip/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_acl_ip/1/delete">' in output.data)

            # Delete Site Admin

            data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post(
                '/host/5/host_acl_ip/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            # Invalid site admin identifier
            output = self.app.post(
                '/host/3/host_acl_ip/2/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host ACL IP not found</p>' in output.data)

            # Delete Site Admin
            output = self.app.post(
                '/host/3/host_acl_ip/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host ACL IP deleted</li>'
                in output.data)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertFalse(
                'action="/host/3/host_acl_ip/1/delete">' in output.data)

    def test_host_netblock_new(self):
        """ Test the host_netblock_new endpoint. """
        output = self.app.get('/host/3/netblock/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/host/3/netblock/new', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/netblock/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            output = self.app.get('/host/3/netblock/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host netblock</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host netblock - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_netblock/2/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'netblock': '192.168.0.0/24',
                'name': 'home network',
            }

            # Check CSRF protection

            output = self.app.post('/host/3/netblock/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host netblock</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host netblock - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_netblock/1/delete">' in output.data)

            # Update site

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/3/netblock/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host netblock added</li>' in output.data)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_netblock/2/delete">' in output.data)

    def test_host_netblock_delete(self):
        """ Test the host_netblock_delete endpoint. """
        output = self.app.post('/host/3/host_netblock/1/delete')
        self.assertEqual(output.status_code, 302)
        output = self.app.post(
            '/host/3/host_netblock/1/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/host/3')
            self.assertEqual(output.status_code, 200)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_netblock/1/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {}

            # Check CSRF protection

            output = self.app.post(
                '/host/3/host_netblock/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_netblock/1/delete">' in output.data)

            # Delete Site Admin

            data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post(
                '/host/5/host_netblock/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            # Invalid site admin identifier
            output = self.app.post(
                '/host/3/host_netblock/2/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host netblock not found</p>' in output.data)

            # Delete Site Admin
            output = self.app.post(
                '/host/3/host_netblock/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host netblock deleted</li>'
                in output.data)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertFalse(
                'action="/host/3/host_netblock/1/delete">' in output.data)

    def test_host_asn_new(self):
        """ Test the host_asn_new endpoint. """
        output = self.app.get('/host/3/asn/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/host/3/asn/new', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/asn/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            output = self.app.get('/host/3/asn/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host Peer ASNs</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Peer ASN - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_asn/2/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'asn': '192168',
                'name': 'ASN pingoured',
            }

            # Check CSRF protection

            output = self.app.post('/host/3/asn/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host Peer ASNs</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Peer ASN - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_asn/2/delete">' in output.data)

            # Update site

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/3/asn/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host Peer ASN added</li>' in output.data)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_asn/2/delete">' in output.data)

    def test_host_asn_delete(self):
        """ Test the host_asn_delete endpoint. """
        output = self.app.post('/host/3/host_asn/1/delete')
        self.assertEqual(output.status_code, 302)
        output = self.app.post(
            '/host/3/host_asn/1/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/host/3')
            self.assertEqual(output.status_code, 200)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_asn/1/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {}

            # Check CSRF protection

            output = self.app.post('/host/3/host_asn/1/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_asn/1/delete">' in output.data)

            # Delete Host ASN

            data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post('/host/5/host_asn/1/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            # Invalid Host ASN identifier
            output = self.app.post('/host/3/host_asn/2/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host Peer ASN not found</p>' in output.data)

            # Delete Host ASN
            output = self.app.post(
                '/host/3/host_asn/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host Peer ASN deleted</li>'
                in output.data)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertFalse(
                'action="/host/3/host_asn/1/delete">' in output.data)

    def test_host_country_new(self):
        """ Test the host_country_new endpoint. """
        output = self.app.get('/host/5/country/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/host/5/country/new', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/country/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            output = self.app.get('/host/3/country/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host country allowed</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Country - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_country/3/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'country': 'GB',
            }

            # Check CSRF protection

            output = self.app.post('/host/3/country/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host country allowed</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Country - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_country/3/delete">' in output.data)

            # Invalid Country code

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/3/country/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Invalid country code</li>'
                in output.data)
            self.assertTrue(
                '<h2>Add host country allowed</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Country - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/host_country/3/delete">' in output.data)

            # Create Country

            data['country'] = 'FR'

            output = self.app.post('/host/3/country/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host Country added</li>' in output.data)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/host_country/3/delete">' in output.data)

    def test_host_country_delete(self):
        """ Test the host_country_delete endpoint. """
        output = self.app.post('/host/1/host_country/1/delete')
        self.assertEqual(output.status_code, 302)
        output = self.app.post(
            '/host/1/host_country/2/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before adding the host
            output = self.app.get('/host/1')
            self.assertEqual(output.status_code, 200)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host mirror.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            #print output.data
            self.assertTrue(
                'action="/host/1/host_country/1/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {}

            # Check CSRF protection

            output = self.app.post('/host/1/host_country/1/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host mirror.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/1/host_country/1/delete">' in output.data)

            # Delete Host Country

            data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post('/host/5/host_country/1/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            # Invalid Host Country identifier
            output = self.app.post('/host/1/host_country/5/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host Country not found</p>' in output.data)

            # Delete Host Country
            output = self.app.post(
                '/host/1/host_country/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host Country deleted</li>'
                in output.data)
            self.assertTrue('<h2>Host mirror.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertFalse(
                'action="/host/1/host_country/1/delete">' in output.data)

    def test_host_category_new(self):
        """ Test the host_category_new endpoint. """
        output = self.app.get('/host/5/category/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/host/5/category/new', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/category/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            output = self.app.get('/host/3/category/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Category - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/category/1/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'category_id': 'Fedora Linux',
            }

            # Invalid input

            output = self.app.post('/host/3/category/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Category - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/category/1/delete">' in output.data)
            self.assertTrue(
                'Not a valid choice<br />Field must contain a number'
                in output.data)

            # Check CSRF protection

            output = self.app.post('/host/3/category/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Category - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/category/1/delete">' in output.data)

            # Add Category

            data['csrf_token'] = csrf_token
            data['category_id'] = '1'

            output = self.app.post('/host/3/category/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host Category added</li>' in output.data)
            self.assertTrue('<h2>Host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in output.data)

            #Try adding the same Category -- fails

            output = self.app.post('/host/3/category/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Could not add Category to the host</li>'
                in output.data)
            self.assertTrue(
                '<h2>Add host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/host/3">' in output.data)
            self.assertTrue(
                '<title>New Host Category - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/3/category/1/delete">' in output.data)

            # Check host after adding the category
            output = self.app.get('/host/3')
            self.assertEqual(output.status_code, 200)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host private.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/3/category/5/delete">' in output.data)

    def test_host_category_delete(self):
        """ Test the host_category_delete endpoint. """
        output = self.app.post('/host/1/category/1/delete')
        self.assertEqual(output.status_code, 302)
        output = self.app.post(
            '/host/1/category/1/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before deleting the category
            output = self.app.get('/host/1')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host mirror.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/1/category/1/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {}

            # Check CSRF protection

            output = self.app.post('/host/1/category/1/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host mirror.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/1/category/1/delete">' in output.data)

            # Delete Host Category

            data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post('/host/5/category/1/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            # Invalid Host Category identifier
            output = self.app.post('/host/1/category/50/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host/Category not found</p>' in output.data)

            # Invalid Host/Category association
            output = self.app.post('/host/1/category/3/delete', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue(
                '<p>Category not associated with this host</p>'
                in output.data)

            # Delete Host Category
            output = self.app.post(
                '/host/1/category/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host Category deleted</li>'
                in output.data)
            self.assertTrue('<h2>Host mirror.localhost</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host - MirrorManager</title>' in output.data)
            self.assertFalse(
                'action="/host/1/category/1/delete">' in output.data)

    def test_host_category_url_new(self):
        """ Test the host_category_url_new endpoint. """
        output = self.app.get('/host/1/category/1/url/new')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/host/1/category/1/url/new', follow_redirects=True)

        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/category/1/url/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            output = self.app.get('/host/1/category/50/url/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host/Category not found</p>' in output.data)

            output = self.app.get('/host/1/category/3/url/new')
            self.assertEqual(output.status_code, 404)
            self.assertTrue(
                '<p>Category not associated with this host</p>'
                in output.data)

            output = self.app.get('/host/1/category/1/url/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host category URL</h2>' in output.data)
            self.assertTrue(
                'test-mirror</a> / <a href="/host/1">' in output.data)
            self.assertTrue(
                '<title>New Host Category URL - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/1/category/1/url/5/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'url': 'http://pingoured.fr/pub/Fedora/',
            }

            # Check CSRF protection

            output = self.app.post('/host/1/category/1/url/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Add host category URL</h2>' in output.data)
            self.assertTrue(
                'test-mirror</a> / <a href="/host/1">' in output.data)
            self.assertTrue(
                '<title>New Host Category URL - MirrorManager</title>'
                in output.data)
            self.assertFalse(
                'action="/host/1/category/1/url/5/delete">' in output.data)

            # Add Host Category URL

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/1/category/1/url/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host Category URL added</li>'
                in output.data)
            self.assertTrue('<h2>Host category</h2>' in output.data)
            self.assertTrue(
                'test-mirror</a> / <a href="/host/1">' in output.data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/1/category/1/url/5/delete">' in output.data)

            # Try adding the same Host Category URL -- fails

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/1/category/1/url/new', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="message">Could not add Category URL to the host</li>'
                in output.data)
            self.assertTrue('<h2>Host category</h2>' in output.data)
            self.assertTrue(
                'test-mirror</a> / <a href="/host/1">' in output.data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/1/category/1/url/5/delete">' in output.data)

    def test_host_category_url_delete(self):
        """ Test the host_category_url_delete endpoint. """
        output = self.app.post('/host/1/category/1/url/3/delete')
        self.assertEqual(output.status_code, 302)
        output = self.app.post(
            '/host/1/category/1/url/3/delete', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):

            # Check before deleting the category URL
            output = self.app.get('/host/1/category/1')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/1/category/1/url/3/delete">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {}

            # Check CSRF protection

            output = self.app.post(
                '/host/1/category/1/url/3/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in output.data)
            self.assertTrue(
                'action="/host/1/category/1/url/3/delete">' in output.data)

            # Delete Host Category URL

            data['csrf_token'] = csrf_token

            # Invalid site identifier
            output = self.app.post(
                '/host/5/category/5/url/5/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            # Invalid Host Category identifier
            output = self.app.post(
                '/host/3/category/50/url/5/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host/Category not found</p>' in output.data)

            # Invalid Host/Category association
            output = self.app.post(
                '/host/1/category/3/url/4/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue(
                '<p>Category not associated with this host</p>'
                in output.data)

            # Invalid Category/URL
            output = self.app.post(
                '/host/1/category/1/url/50/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue(
                '<p>Host category URL not found</p>'
                in output.data)

            # Invalid Category/URL association
            output = self.app.post(
                '/host/1/category/2/url/4/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 404)
            self.assertTrue(
                '<p>Category URL not associated with this host</p>'
                in output.data)

            # Delete Host Category URL
            output = self.app.post(
                '/host/1/category/1/url/3/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Host category URL deleted</li>'
                in output.data)
            self.assertTrue('<h2>Host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/1">' in output.data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>' in output.data)
            self.assertFalse(
                'action="/host/1/category/1/url/3/delete">' in output.data)

    def test_host_category(self):
        """ Test the host_category endpoint. """

        output = self.app.post('/host/2/category/5')
        self.assertEqual(output.status_code, 302)
        output = self.app.post('/host/2/category/5', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/host/50/category/5')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host not found</p>' in output.data)

            output = self.app.get('/host/3/category/50')
            self.assertEqual(output.status_code, 404)
            self.assertTrue('<p>Host/Category not found</p>' in output.data)

            output = self.app.get('/host/3/category/2')
            self.assertEqual(output.status_code, 404)
            self.assertTrue(
                '<p>Category not associated with this host</p>'
                in output.data)

            output = self.app.get('/host/2/category/3')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<input id="always_up2date" name="always_up2date" '
                'type="checkbox" value="y">' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {'always_up2date': ''}

            # Check CSRF protection

            output = self.app.post('/host/2/category/3', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/2">' in output.data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in output.data)
            self.assertTrue(
                '<input id="always_up2date" name="always_up2date" '
                'type="checkbox" value="">' in output.data)

            # Update Host Category

            data['csrf_token'] = csrf_token

            output = self.app.post('/host/2/category/3', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Host category</h2>' in output.data)
            self.assertTrue('Back to <a href="/site/2">' in output.data)
            self.assertTrue(
                '<title>Host Category - MirrorManager</title>'
                in output.data)
            self.assertTrue(
                '<input id="always_up2date" name="always_up2date" '
                'type="checkbox" value="y">' in output.data)
            self.assertTrue(
                '<li class="message">Host Category updated</li>'
                in output.data)

    def test_auth_logout(self):
        """ Test the auth_logout endpoint. """
        output = self.app.get('/logout')
        self.assertEqual(output.status_code, 302)
        output = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h2>Fedora Public Active Mirrors</h2>' in output.data)

        user = tests.FakeFasUser()
        with tests.user_set(mirrormanager2.app.APP, user):
            output = self.app.get('/logout')
            self.assertEqual(output.status_code, 302)
            output = self.app.get('/logout', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">You are no longer logged-in</li>'
                in output.data)
            self.assertTrue(
                '<h2>Fedora Public Active Mirrors</h2>' in output.data)

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAppTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
