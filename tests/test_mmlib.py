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
        self.assertEqual(len(results), 0)

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategoryurl(self.session)
        tests.create_categorydirectory(self.session)

        results = mirrormanager2.lib.query_directories(self.session)
        self.assertEqual(len(results), 12)

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

    def test_get_host_acl_ip(self):
        """ Test the get_host_acl_ip function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_host_acl_ip(self.session, 1)
        self.assertEqual(results, None)

        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_hostaclip(self.session)

        results = mirrormanager2.lib.get_host_acl_ip(self.session, 1)
        self.assertEqual(results.host.name, 'mirror.localhost')
        self.assertEqual(results.host.country, 'US')
        results = mirrormanager2.lib.get_host_acl_ip(self.session, 2)
        self.assertEqual(results.host.name, 'mirror2.localhost')
        self.assertEqual(results.host.country, 'FR')

    def test_get_host_netblock(self):
        """ Test the get_host_netblock function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_host_netblock(self.session, 1)
        self.assertEqual(results, None)

        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_hostnetblock(self.session)

        results = mirrormanager2.lib.get_host_netblock(self.session, 1)
        self.assertEqual(results.host.name, 'private.localhost')
        self.assertEqual(results.host.country, 'NL')
        results = mirrormanager2.lib.get_host_netblock(self.session, 2)
        self.assertEqual(results, None)

    def test_get_host_peer_asn(self):
        """ Test the get_host_peer_asn function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_host_peer_asn(self.session, 1)
        self.assertEqual(results, None)

        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_hostpeerasn(self.session)

        results = mirrormanager2.lib.get_host_peer_asn(self.session, 1)
        self.assertEqual(results.host.name, 'private.localhost')
        self.assertEqual(results.host.country, 'NL')
        results = mirrormanager2.lib.get_host_peer_asn(self.session, 2)
        self.assertEqual(results, None)

    def test_get_host_country(self):
        """ Test the get_host_country function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_host_country(self.session, 1)
        self.assertEqual(results, None)

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_hostcountry(self.session)

        results = mirrormanager2.lib.get_host_country(self.session, 1)
        self.assertEqual(results.host.name, 'mirror.localhost')
        self.assertEqual(results.host.country, 'US')
        results = mirrormanager2.lib.get_host_country(self.session, 2)
        self.assertEqual(results.host.name, 'mirror2.localhost')
        self.assertEqual(results.host.country, 'FR')
        results = mirrormanager2.lib.get_host_country(self.session, 3)
        self.assertEqual(results, None)

    def test_get_host_category(self):
        """ Test the get_host_category function of mirrormanager2.lib. """
        results = mirrormanager2.lib.get_host_category(self.session, 1)
        self.assertEqual(results, None)

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)

        results = mirrormanager2.lib.get_host_category(self.session, 1)
        self.assertEqual(results.host.name, 'mirror.localhost')
        self.assertEqual(results.host.country, 'US')
        results = mirrormanager2.lib.get_host_category(self.session, 2)
        self.assertEqual(results.host.name, 'mirror.localhost')
        self.assertEqual(results.host.country, 'US')
        results = mirrormanager2.lib.get_host_category(self.session, 3)
        self.assertEqual(results.host.name, 'mirror2.localhost')
        self.assertEqual(results.host.country, 'FR')
        results = mirrormanager2.lib.get_host_category(self.session, 4)
        self.assertEqual(results.host.name, 'mirror2.localhost')
        self.assertEqual(results.host.country, 'FR')
        results = mirrormanager2.lib.get_host_category(self.session, 5)
        self.assertEqual(results, None)

    def test_get_host_category_by_hostid_category(self):
        """ Test the get_host_category_by_hostid_category function of
        mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_host_category_by_hostid_category(
            self.session, 1, 'Fedora Linux')
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)

        results = mirrormanager2.lib.get_host_category_by_hostid_category(
            self.session, 1, 'Fedora Linux')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].host.name, 'mirror.localhost')
        self.assertEqual(results[0].host.country, 'US')

        results = mirrormanager2.lib.get_host_category_by_hostid_category(
            self.session, 2, 'Fedora Linux')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].host.name, 'mirror2.localhost')
        self.assertEqual(results[0].host.country, 'FR')

        results = mirrormanager2.lib.get_host_category_by_hostid_category(
            self.session, 3, 'Fedora Linux')
        self.assertEqual(results, [])

    def test_get_host_category_url_by_id(self):
        """ Test the get_host_category_url_by_id function of
        mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_host_category_url_by_id(
            self.session, 1)
        self.assertEqual(results, None)

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategoryurl(self.session)

        for i in range(4):
            results = mirrormanager2.lib.get_host_category_url_by_id(
                self.session, i+1)
            self.assertEqual(
                results.host_category.host.name, 'mirror.localhost')
            self.assertEqual(
                results.host_category.host.country, 'US')

        results = mirrormanager2.lib.get_host_category_url_by_id(
            self.session, 5)
        self.assertEqual(results, None)

    def test_get_host_category_url(self):
        """ Test the get_host_category_url function of
        mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_host_category_url(self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategoryurl(self.session)

        results = mirrormanager2.lib.get_host_category_url(self.session)
        self.assertEqual(len(results), 4)
        for i in range(4):
            self.assertEqual(
                results[i].host_category.host.name, 'mirror.localhost')
            self.assertEqual(
                results[i].host_category.host.country, 'US')

    def test_get_country_by_name(self):
        """ Test the get_country_by_name function of
        mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_country_by_name(self.session, 'FR')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)

        for i in ['FR', 'US']:
            results = mirrormanager2.lib.get_country_by_name(
                self.session, i)
            self.assertEqual(results.code, i)

        results = mirrormanager2.lib.get_country_by_name(self.session, 'BE')
        self.assertEqual(results, None)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MMLibtests)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
