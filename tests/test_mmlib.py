# -*- coding: utf-8 -*-

'''
mirrormanager2 tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import mirrormanager2.lib
import tests


class MMLibtests(tests.Modeltests):
    """ Collection tests. """

    def test_query_directories(self):
        """ Test the query_directories function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.query_directories(self.session)
        cnt = 0
        for row in results:
            if cnt == 0:
                print '**', row
                self.assertEqual(row.directory_id, 3764)
                self.assertEqual(row.dname, 'pub/alt')
                self.assertEqual(row.hostid, 271)
                self.assertEqual(row.country, 'US')
                self.assertEqual(row.id, 6817)
            cnt += 1
        self.assertEqual(cnt, 1693670)

    def test_get_site(self):
        """ Test the get_site function of mirrormanager2.lib. """
        tests.create_site(self.session)

        results = mirrormanager2.lib.get_site(self.session, 0)
        self.assertEqual(results, None)

        results = mirrormanager2.lib.get_site(self.session, 1)
        self.assertEqual(results.name, 'test-mirror')
        self.assertEqual(results.private, False)
        self.assertEqual(results.created_by, 'pingou')

        results = mirrormanager2.lib.get_site(self.session, 2)
        self.assertEqual(results.name, 'test-mirror2')
        self.assertEqual(results.private, False)
        self.assertEqual(results.created_by, 'kevin')

        results = mirrormanager2.lib.get_site(self.session, 3)
        self.assertEqual(results.name, 'test-mirror_private')
        self.assertEqual(results.private, True)
        self.assertEqual(results.created_by, 'skvidal')

    def test_get_site_by_name(self):
        """ Test the get_site_by_name function of mirrormanager2.lib. """
        tests.create_site(self.session)

        results = mirrormanager2.lib.get_site_by_name(self.session, 'foo')
        self.assertEqual(results, None)

        results = mirrormanager2.lib.get_site_by_name(
            self.session, 'test-mirror')
        self.assertEqual(results.name, 'test-mirror')
        self.assertEqual(results.private, False)
        self.assertEqual(results.created_by, 'pingou')

        results = mirrormanager2.lib.get_site_by_name(
            self.session, 'test-mirror2')
        self.assertEqual(results.name, 'test-mirror2')
        self.assertEqual(results.private, False)
        self.assertEqual(results.created_by, 'kevin')

    def test_get_all_sites(self):
        """ Test the get_all_sites function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_all_sites(self.session)
        self.assertEqual(results, [])

        tests.create_site(self.session)

        results = mirrormanager2.lib.get_all_sites(self.session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'test-mirror')
        self.assertEqual(results[1].name, 'test-mirror2')
        self.assertEqual(results[2].name, 'test-mirror_private')

    def test_get_siteadmin(self):
        """ Test the get_siteadmin function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_siteadmin(self.session, 1)
        self.assertEqual(results, None)

        tests.create_site(self.session)

        results = mirrormanager2.lib.get_siteadmin(self.session, 1)
        self.assertEqual(results, None)

        tests.create_site_admin(self.session)

        results = mirrormanager2.lib.get_siteadmin(self.session, 1)
        self.assertEqual(results.site.name, 'test-mirror')
        self.assertEqual(results.username, 'ralph')

        results = mirrormanager2.lib.get_siteadmin(self.session, 4)
        self.assertEqual(results.site.name, 'test-mirror2')
        self.assertEqual(results.username, 'pingou')

    def test_get_host(self):
        """ Test the get_host function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_host(self.session, 1)
        self.assertEqual(results, None)

        tests.create_site(self.session)
        tests.create_hosts(self.session)

        results = mirrormanager2.lib.get_host(self.session, 1)
        self.assertEqual(results.name, 'mirror.localhost')
        self.assertEqual(results.country, 'US')

        results = mirrormanager2.lib.get_host(self.session, 2)
        self.assertEqual(results.name, 'mirror2.localhost')
        self.assertEqual(results.country, 'FR')

        results = mirrormanager2.lib.get_host(self.session, 3)
        self.assertEqual(results.name, 'private.localhost')
        self.assertEqual(results.country, 'NL')

    def test_get_hosts(self):
        """ Test the get_hosts function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_hosts(self.session)
        self.assertEqual(results, [])

        tests.create_site(self.session)
        tests.create_hosts(self.session)

        results = mirrormanager2.lib.get_hosts(self.session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror.localhost')
        self.assertEqual(results[0].country, 'US')
        self.assertEqual(results[1].name, 'mirror2.localhost')
        self.assertEqual(results[1].country, 'FR')
        self.assertEqual(results[2].name, 'private.localhost')
        self.assertEqual(results[2].country, 'NL')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MMLibtests)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
