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

    def test_get_country_continent_redirect(self):
        """ Test the get_country_continent_redirect function of
        mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_country_continent_redirect(
            self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_country_continent_redirect(
                self.session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].country, 'IL')
        self.assertEqual(results[0].continent, 'EU')
        self.assertEqual(results[1].country, 'AM')
        self.assertEqual(results[1].continent, 'EU')
        self.assertEqual(results[2].country, 'JO')
        self.assertEqual(results[2].continent, 'EU')

    def test_get_user_by_username(self):
        """ Test the get_user_by_username function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_user_by_username(
            self.session, 'pingou')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_user_by_username(
                self.session, 'pingou')
        self.assertEqual(results.user_name, 'pingou')
        self.assertEqual(results.email_address, 'pingou@fp.o')

        results = mirrormanager2.lib.get_user_by_username(
                self.session, 'ralph')
        self.assertEqual(results.user_name, 'ralph')
        self.assertEqual(results.email_address, 'ralph@fp.o')

        results = mirrormanager2.lib.get_user_by_username(
                self.session, 'foo')
        self.assertEqual(results, None)

    def test_get_user_by_email(self):
        """ Test the get_user_by_email function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_user_by_email(
            self.session, 'pingou@fp.o')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_user_by_email(
                self.session, 'pingou@fp.o')
        self.assertEqual(results.user_name, 'pingou')
        self.assertEqual(results.email_address, 'pingou@fp.o')

        results = mirrormanager2.lib.get_user_by_email(
                self.session, 'ralph@fp.o')
        self.assertEqual(results.user_name, 'ralph')
        self.assertEqual(results.email_address, 'ralph@fp.o')

        results = mirrormanager2.lib.get_user_by_email(
                self.session, 'foo')
        self.assertEqual(results, None)

    def test_get_user_by_token(self):
        """ Test the get_user_by_token function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_user_by_token(
            self.session, 'bar')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_user_by_token(
                self.session, 'bar')
        self.assertEqual(results.user_name, 'shaiton')
        self.assertEqual(results.email_address, 'shaiton@fp.o')

        results = mirrormanager2.lib.get_user_by_token(
                self.session, 'foo')
        self.assertEqual(results, None)

    def test_get_session_by_visitkey(self):
        """ Test the get_session_by_visitkey function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_session_by_visitkey(
            self.session, 'foo')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_session_by_visitkey(
                self.session, 'foo')
        self.assertEqual(results.user.user_name, 'pingou')
        self.assertEqual(results.user.email_address, 'pingou@fp.o')
        self.assertEqual(results.user_ip, '127.0.0.1')

        results = mirrormanager2.lib.get_session_by_visitkey(
                self.session, 'bar')
        self.assertEqual(results, None)

    def test_get_version_by_name_version(self):
        """ Test the get_version_by_name_version function of
        mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_version_by_name_version(
            self.session, 'Fedora', '21')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)
        tests.create_version(self.session)

        results = mirrormanager2.lib.get_version_by_name_version(
            self.session, 'Fedora', 21)
        self.assertEqual(results.product.name, 'Fedora')
        self.assertEqual(results.name, '21')

        results = mirrormanager2.lib.get_version_by_name_version(
            self.session, 'Fedora', '21-alpha')
        self.assertEqual(results.product.name, 'Fedora')
        self.assertEqual(results.name, '21-alpha')
        self.assertEqual(results.is_test, True)

        results = mirrormanager2.lib.get_session_by_visitkey(
                self.session, 'bar')
        self.assertEqual(results, None)

    def test_get_versions(self):
        """ Test the get_versions function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_versions(self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_version(self.session)

        results = mirrormanager2.lib.get_versions(self.session)
        self.assertEqual(len(results), 6)
        self.assertEqual(results[0].product.name, 'Fedora')
        self.assertEqual(results[0].name, '20')
        self.assertEqual(results[1].product.name, 'Fedora')
        self.assertEqual(results[1].name, '21-alpha')
        self.assertEqual(results[2].product.name, 'Fedora')
        self.assertEqual(results[2].name, '21')

    def test_get_arch_by_name(self):
        """ Test the get_arch_by_name function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_arch_by_name(self.session, 'i386')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_arch_by_name(self.session, 'i386')
        self.assertEqual(results.name, 'i386')

        results = mirrormanager2.lib.get_arch_by_name(self.session, 'i686')
        self.assertEqual(results, None)

    def test_get_categories(self):
        """ Test the get_categories function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_categories(self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)

        results = mirrormanager2.lib.get_categories(self.session)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'Fedora Linux')
        self.assertEqual(results[0].product.name, 'Fedora')
        self.assertEqual(results[1].name, 'Fedora EPEL')
        self.assertEqual(results[1].product.name, 'EPEL')

    def test_get_category_by_name(self):
        """ Test the get_category_by_name function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_category_by_name(
            self.session, 'Fedora EPEL')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)

        results = mirrormanager2.lib.get_category_by_name(
            self.session, 'Fedora EPEL')
        self.assertEqual(results.name, 'Fedora EPEL')
        self.assertEqual(results.product.name, 'EPEL')

        results = mirrormanager2.lib.get_category_by_name(
            self.session, 'Fedora Linux')
        self.assertEqual(results.name, 'Fedora Linux')
        self.assertEqual(results.product.name, 'Fedora')

        results = mirrormanager2.lib.get_category_by_name(
            self.session, 'foo')
        self.assertEqual(results, None)

    def test_get_category_directory(self):
        """ Test the get_category_directory function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_category_directory(self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)

        results = mirrormanager2.lib.get_category_directory(self.session)
        self.assertEqual(len(results), 4)
        self.assertEqual(
            results[0].category.name, 'Fedora Linux')
        self.assertEqual(
            results[0].directory.name, 'pub/fedora/linux/releases')
        self.assertEqual(
            results[1].category.name, 'Fedora EPEL')
        self.assertEqual(
            results[1].directory.name, 'pub/epel')

    def test_get_product_by_name(self):
        """ Test the get_product_by_name function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_product_by_name(
            self.session, 'Fedora')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_product_by_name(
            self.session, 'Fedora')
        self.assertEqual(results.name, 'Fedora')

        results = mirrormanager2.lib.get_product_by_name(
            self.session, 'EPEL')
        self.assertEqual(results.name, 'EPEL')

        results = mirrormanager2.lib.get_product_by_name(
            self.session, 'foo')
        self.assertEqual(results, None)

    def test_get_products(self):
        """ Test the get_products function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_products(self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_products(self.session)
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0].name, 'EPEL')
        self.assertEqual(
            results[1].name, 'Fedora')

    def test_get_repo_prefix_arch(self):
        """ Test the get_repo_prefix_arch function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_repo_prefix_arch(
            self.session, 'updates-testing-f20', 'x86_64')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)
        tests.create_version(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_repository(self.session)

        results = mirrormanager2.lib.get_repo_prefix_arch(
            self.session, 'updates-testing-f20', 'x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/20/x86_64')

        results = mirrormanager2.lib.get_repo_prefix_arch(
            self.session, 'updates-testing-f21', 'x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/21/x86_64')

        results = mirrormanager2.lib.get_repo_prefix_arch(
            self.session, 'updates-testing-f20', 'i386')
        self.assertEqual(results, None)

    def test_get_repo_by_name(self):
        """ Test the get_repo_by_name function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_repo_by_name(
            self.session, 'pub/fedora/linux/updates/testing/19/x86_64')
        self.assertEqual(results, None)

        tests.create_base_items(self.session)
        tests.create_version(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_repository(self.session)

        results = mirrormanager2.lib.get_repo_by_name(
            self.session, 'pub/fedora/linux/updates/testing/19/x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/19/x86_64')

        results = mirrormanager2.lib.get_repo_by_name(
            self.session, 'pub/fedora/linux/updates/testing/20/x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/20/x86_64')

        results = mirrormanager2.lib.get_repo_by_name(
            self.session, 'pub/fedora/linux/updates/testing/19/i386')
        self.assertEqual(results, None)

    def test_get_repo_by_dir(self):
        """ Test the get_repo_by_dir function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_repo_by_dir(
            self.session, 'pub/fedora/linux/updates/testing/21/x86_64')
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_version(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_repository(self.session)

        results = mirrormanager2.lib.get_repo_by_dir(
            self.session, 'pub/fedora/linux/updates/testing/21/x86_64')
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].name, 'pub/fedora/linux/updates/testing/21/x86_64')
        self.assertEqual(results[0].arch.name, 'x86_64')

    def test_get_repositories(self):
        """ Test the get_repositories function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_version(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_repository(self.session)

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 3)
        self.assertEqual(
            results[0].name, 'pub/fedora/linux/updates/testing/19/x86_64')
        self.assertEqual(results[0].arch.name, 'x86_64')

        self.assertEqual(
            results[1].name, 'pub/fedora/linux/updates/testing/20/x86_64')
        self.assertEqual(results[1].arch.name, 'x86_64')

        self.assertEqual(
            results[2].name, 'pub/fedora/linux/updates/testing/21/x86_64')
        self.assertEqual(results[2].arch.name, 'x86_64')

    def test_get_reporedirect(self):
        """ Test the get_reporedirect function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_reporedirect(self.session)
        self.assertEqual(results, [])

        tests.create_repositoryredirect(self.session)

        results = mirrormanager2.lib.get_reporedirect(self.session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].from_repo, 'fedora-rawhide')
        self.assertEqual(results[0].to_repo, 'rawhide')
        self.assertEqual(results[1].from_repo, 'fedora-install-rawhide')
        self.assertEqual(results[1].to_repo, 'rawhide')
        self.assertEqual(results[2].from_repo, 'epel-6.0')
        self.assertEqual(results[2].to_repo, 'epel-6')

    def test_get_arches(self):
        """ Test the get_arches function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_arches(self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)

        results = mirrormanager2.lib.get_arches(self.session)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].name, 'i386')
        self.assertEqual(results[1].name, 'ppc')
        self.assertEqual(results[2].name, 'source')
        self.assertEqual(results[3].name, 'x86_64')

    def test_add_admin_to_site(self):
        """ Test the add_admin_to_site function of mirrormanager2.lib.
        """
        tests.create_base_items(self.session)
        tests.create_site(self.session)

        site = mirrormanager2.lib.get_site(self.session, 1)

        results = mirrormanager2.lib.add_admin_to_site(
            self.session, site, 'pingou')
        self.assertEqual(results, 'pingou added as an admin')

        results = mirrormanager2.lib.add_admin_to_site(
            self.session, site, 'pingou')
        self.assertEqual(results, 'pingou was already listed as an admin')

    def test_get_locations(self):
        """ Test the get_locations function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_locations(self.session)
        self.assertEqual(results, [])

        tests.create_location(self.session)

        results = mirrormanager2.lib.get_locations(self.session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'foo')
        self.assertEqual(results[1].name, 'bar')
        self.assertEqual(results[2].name, 'foobar')

    def test_get_netblock_country(self):
        """ Test the get_netblock_country function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_netblock_country(self.session)
        self.assertEqual(results, [])

        tests.create_netblockcountry(self.session)

        results = mirrormanager2.lib.get_netblock_country(self.session)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].netblock, '127.0.0.0/24')
        self.assertEqual(results[0].country, 'AU')

    def test_get_mirrors(self):
        """ Test the get_mirrors function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_mirrors(self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategoryurl(self.session)
        tests.create_categorydirectory(self.session)
        tests.create_netblockcountry(self.session)

        results = mirrormanager2.lib.get_mirrors(self.session)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(self.session, private=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'private.localhost')

        results = mirrormanager2.lib.get_mirrors(self.session, internet2=True)
        self.assertEqual(len(results), 0)

        results = mirrormanager2.lib.get_mirrors(
            self.session, internet2_clients=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, internet2_clients=False)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, asn_clients=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        results = mirrormanager2.lib.get_mirrors(
            self.session, asn_clients=False)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'private.localhost')
        self.assertEqual(results[1].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, admin_active=False)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, admin_active=True)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, user_active=False)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, user_active=True)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, host_category_url_private=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, host_category_url_private=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, last_crawl_duration=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, last_crawl_duration=False)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, last_crawled=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, last_crawled=False)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, last_checked_in=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, last_checked_in=False)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, site_private=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, site_private=False)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, site_user_active=False)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, site_user_active=True)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, site_admin_active=False)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, site_admin_active=True)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'private.localhost')
        self.assertEqual(results[2].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, up2date=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, up2date=False)
        self.assertEqual(len(results), 0)

        results = mirrormanager2.lib.get_mirrors(
            self.session, version_id=1)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, version_id=3)

        tests.create_version(self.session)
        tests.create_repository(self.session)

        results = mirrormanager2.lib.get_mirrors(
            self.session, version_id=1)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'mirror.localhost')
        results = mirrormanager2.lib.get_mirrors(
            self.session, version_id=3)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'mirror.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, arch_id=1)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, arch_id=3)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        self.assertEqual(results[1].name, 'mirror.localhost')


    def test_get_user_sites(self):
        """ Test the get_user_sites function or mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_user_sites(self.session, 'pingou')
        self.assertEqual(results, [])

        self.test_add_admin_to_site()

        results = mirrormanager2.lib.get_user_sites(self.session, 'pingou')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'test-mirror')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MMLibtests)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
