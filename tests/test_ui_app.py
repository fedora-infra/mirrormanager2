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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskUiAppTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
