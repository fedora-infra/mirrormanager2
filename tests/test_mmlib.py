# -*- coding: utf-8 -*-

'''
mirrormanager2 tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os
import mirrormanager2.lib
import mirrormanager2.lib.mirrorlist
import mirrormanager2.lib.mirrormanager_pb2
import tests
import tempfile
import datetime
import pickle
from IPy import IP


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
        self.assertEqual(len(results), 4)
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
                self.session, i + 1)
            self.assertEqual(
                results.host_category.host.name, 'mirror.localhost')
            self.assertEqual(
                results.host_category.host.country, 'US')

        results = mirrormanager2.lib.get_host_category_url_by_id(
            self.session, 9)
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
        self.assertEqual(len(results), 8)
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
            self.session, 'Fedora', 27)
        self.assertEqual(results.product.name, 'Fedora')
        self.assertEqual(results.name, '27')

        results = mirrormanager2.lib.get_version_by_name_version(
            self.session, 'Fedora', '27-alpha')
        self.assertEqual(results.product.name, 'Fedora')
        self.assertEqual(results.name, '27-alpha')
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
        self.assertEqual(results[0].name, '26')
        self.assertEqual(results[1].product.name, 'Fedora')
        self.assertEqual(results[1].name, '27-alpha')
        self.assertEqual(results[2].product.name, 'Fedora')
        self.assertEqual(results[2].name, '27')

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
            results[0].directory.name, 'pub/fedora/linux')
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
            self.session, 'updates-testing-f26', 'x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/26/x86_64')

        results = mirrormanager2.lib.get_repo_prefix_arch(
            self.session, 'updates-testing-f27', 'x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/27/x86_64')

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
            self.session, 'pub/fedora/linux/updates/testing/25/x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/25/x86_64')

        results = mirrormanager2.lib.get_repo_by_name(
            self.session, 'pub/fedora/linux/updates/testing/26/x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/26/x86_64')

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
            self.session, 'pub/fedora/linux/updates/testing/27/x86_64')
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].name, 'pub/fedora/linux/updates/testing/27/x86_64')
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
        self.assertEqual(len(results), 4)
        self.assertEqual(
            results[0].name, 'pub/fedora/linux/updates/testing/25/x86_64')
        self.assertEqual(results[0].arch.name, 'x86_64')

        self.assertEqual(
            results[1].name, 'pub/fedora/linux/updates/testing/26/x86_64')
        self.assertEqual(results[1].arch.name, 'x86_64')

        self.assertEqual(
            results[2].name, 'pub/fedora/linux/updates/testing/27/x86_64')
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

    def check_results_host(self, results):
        for result in results:
            if result.id == 1:
                self.assertEqual(result.name, 'mirror.localhost')
            elif result.id == 2:
                self.assertEqual(result.name, 'mirror2.localhost')
            elif result.id == 3:
                self.assertEqual(result.name, 'private.localhost')
            elif result.id == 4:
                self.assertEqual(result.name, 'Another test entry')
            else:
                self.assertTrue(False)

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
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

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
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, asn_clients=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'mirror2.localhost')
        results = mirrormanager2.lib.get_mirrors(
            self.session, asn_clients=False)
        self.assertEqual(len(results), 3)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, admin_active=False)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, admin_active=True)
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, user_active=False)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, user_active=True)
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, host_category_url_private=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, host_category_url_private=False)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'mirror2.localhost')

        results = mirrormanager2.lib.get_mirrors(
            self.session, last_crawl_duration=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, last_crawl_duration=False)
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, last_crawled=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, last_crawled=False)
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, last_checked_in=True)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, last_checked_in=False)
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, site_private=True)
        self.assertEqual(len(results), 1)
        results = mirrormanager2.lib.get_mirrors(
            self.session, site_private=False)
        self.assertEqual(len(results), 3)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, site_user_active=False)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, site_user_active=True)
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, site_admin_active=False)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, site_admin_active=True)
        self.assertEqual(len(results), 4)
        self.check_results_host(results)

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
            self.session, version_id=4)

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
        self.check_results_host(results)

        results = mirrormanager2.lib.get_mirrors(
            self.session, arch_id=1)
        self.assertEqual(len(results), 0)
        results = mirrormanager2.lib.get_mirrors(
            self.session, arch_id=3)
        self.assertEqual(len(results), 2)
        self.check_results_host(results)

    def test_get_user_sites(self):
        """ Test the get_user_sites function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_user_sites(self.session, 'pingou')
        self.assertEqual(results, [])

        self.test_add_admin_to_site()

        results = mirrormanager2.lib.get_user_sites(self.session, 'pingou')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'test-mirror')

    def test_id_generator(self):
        """ Test the id_generator function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.id_generator(size=5, chars=['a'])
        self.assertEqual(results, 'aaaaa')

        results = mirrormanager2.lib.id_generator(size=5, chars=['1'])
        self.assertEqual(results, '11111')

    def test_get_directory_by_name(self):
        """ Test the get_directory_by_name function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_directory_by_name(
            self.session, 'pub/epel')
        self.assertEqual(results, None)

        tests.create_directory(self.session)

        results = mirrormanager2.lib.get_directory_by_name(
            self.session, 'pub/epel')
        self.assertEqual(results.name, 'pub/epel')
        self.assertEqual(results.readable, True)

        results = mirrormanager2.lib.get_directory_by_name(
            self.session, 'pub/fedora/linux/extras')
        self.assertEqual(results.name, 'pub/fedora/linux/extras')
        self.assertEqual(results.readable, True)

        results = mirrormanager2.lib.get_directory_by_name(
            self.session, 'pub/fedora/linux/updates/testing/25/x86_64')
        self.assertEqual(
            results.name, 'pub/fedora/linux/updates/testing/25/x86_64')
        self.assertEqual(results.readable, True)

    def test_get_directories(self):
        """ Test the get_directories function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_directories(self.session)
        self.assertEqual(results, [])

        tests.create_directory(self.session)

        results = mirrormanager2.lib.get_directories(self.session)
        self.assertEqual(len(results), 9)
        self.assertEqual(results[0].name, 'pub/fedora/linux')
        self.assertEqual(results[1].name, 'pub/fedora/linux/extras')
        self.assertEqual(results[2].name, 'pub/epel')

    def test_get_directory_by_id(self):
        """ Test the get_directory_by_id function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_directory_by_id(
            self.session, 1)
        self.assertEqual(results, None)

        tests.create_directory(self.session)

        results = mirrormanager2.lib.get_directory_by_id(self.session, 3)
        self.assertEqual(results.name, 'pub/epel')
        self.assertEqual(results.readable, True)

        results = mirrormanager2.lib.get_directory_by_id(self.session, 2)
        self.assertEqual(results.name, 'pub/fedora/linux/extras')
        self.assertEqual(results.readable, True)

        results = mirrormanager2.lib.get_directory_by_id(self.session, 4)
        self.assertEqual(
            results.name, 'pub/fedora/linux/releases/26')
        self.assertEqual(results.readable, True)

    def test_get_hostcategorydir_by_hostcategoryid_and_path(self):
        """ Test the get_hostcategorydir_by_hostcategoryid_and_path
        function of mirrormanager2.lib.
        """
        results = mirrormanager2.lib \
            .get_hostcategorydir_by_hostcategoryid_and_path(
                self.session, 2, 'pub/fedora/linux/releases/21')
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategorydir(self.session)

        results = mirrormanager2.lib \
            .get_hostcategorydir_by_hostcategoryid_and_path(
                self.session, 3, 'pub/fedora/linux/releases/27')
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].directory.name, 'pub/fedora/linux/releases/27')
        self.assertEqual(
            results[0].host_category.category.name, 'Fedora Linux')

    def test_get_directory_exclusive_host(self):
        """ Test the get_directory_exclusive_host function of
        mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_directory_exclusive_host(
            self.session)
        self.assertEqual(results, [])

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_directoryexclusivehost(self.session)

        results = mirrormanager2.lib.get_directory_exclusive_host(
            self.session)
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0].dname, 'pub/fedora/linux/releases/26')
        self.assertEqual(
            results[0].host_id, 1)
        self.assertEqual(
            results[1].dname, 'pub/fedora/linux/releases/27')
        self.assertEqual(
            results[1].host_id, 3)

    def test_get_file_detail(self):
        """ Test the get_file_detail function of
        mirrormanager2.lib.
        """
        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7)
        self.assertEqual(results, None)

        tests.create_directory(self.session)
        tests.create_filedetail(self.session)

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7)
        self.assertEqual(results.md5, 'foo_md5')
        self.assertEqual(
            results.directory.name,
            'pub/fedora/linux/updates/testing/25/x86_64')

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7, md5='foo_md5')
        self.assertEqual(results.md5, 'foo_md5')
        self.assertEqual(
            results.directory.name,
            'pub/fedora/linux/updates/testing/25/x86_64')

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7, sha1='foo_sha1')
        self.assertEqual(results.md5, 'foo_md5')
        self.assertEqual(
            results.directory.name,
            'pub/fedora/linux/updates/testing/25/x86_64')

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7, sha256='foo_sha256')
        self.assertEqual(results.md5, 'foo_md5')
        self.assertEqual(
            results.directory.name,
            'pub/fedora/linux/updates/testing/25/x86_64')

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7, sha512='foo_sha512')
        self.assertEqual(results.md5, 'foo_md5')
        self.assertEqual(
            results.directory.name,
            'pub/fedora/linux/updates/testing/25/x86_64')

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7, size=2973)
        self.assertEqual(results, None)

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7, timestamp=1357758825)
        self.assertEqual(results.md5, 'foo_md5')
        self.assertEqual(
            results.directory.name,
            'pub/fedora/linux/updates/testing/25/x86_64')

    def test_mirrorlist_export(self):
        """ Test the export to mirrorlist by comparing
        the result of pickle and protobuf export.
        """

        tests.create_base_items(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_directory(self.session)
        tests.create_filedetail(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)
        tests.create_directoryexclusivehost(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategoryurl(self.session)
        tests.create_hostcategorydir(self.session)
        tests.create_hostcategorydir_one_more(self.session)
        tests.create_hostcategorydir_even_more(self.session)
        tests.create_hostpeerasn(self.session)
        tests.create_hostnetblock(self.session)
        tests.create_netblockcountry(self.session)
        tests.create_repositoryredirect(self.session)
        tests.create_version(self.session)
        tests.create_repository(self.session)
        tests.create_hostcountry(self.session)
        tests.create_host_country_allowed(self.session)
        # Locations has not been ported to MirrorManager2, does not work
        # tests.create_location(self.session)

        mirrormanager2.lib.mirrorlist.populate_all_caches(self.session)
        fd, path = tempfile.mkstemp()
        mirrormanager2.lib.mirrorlist.dump_caches(
            self.session,
            path,
            path + '.proto'
        )

        f = open(path, 'rb')
        data = pickle.load(f)
        f.close()

        mirrorlist = mirrormanager2.lib.mirrormanager_pb2.MirrorList()
        f = open(path + '.proto', 'rb')
        mirrorlist.ParseFromString(f.read())
        f.close()
        os.remove(path)
        os.remove(path + '.proto')

        self.assertEqual(
            data['time'].year,
            datetime.datetime.fromtimestamp(mirrorlist.Time).year
        )
        self.assertEqual(
            data['time'].month,
            datetime.datetime.fromtimestamp(mirrorlist.Time).month
        )
        self.assertEqual(
            data['time'].day,
            datetime.datetime.fromtimestamp(mirrorlist.Time).day
        )
        self.assertEqual(
            data['time'].hour,
            datetime.datetime.fromtimestamp(mirrorlist.Time).hour
        )
        self.assertEqual(
            data['time'].minute,
            datetime.datetime.fromtimestamp(mirrorlist.Time).minute
        )
        self.assertEqual(
            data['time'].second,
            datetime.datetime.fromtimestamp(mirrorlist.Time).second
        )

        host_asn_cache = {}
        for i, item in enumerate(mirrorlist.HostAsnCache):
            if item.key not in host_asn_cache.keys():
                host_asn_cache[item.key] = []
            for v, value in enumerate(item.value):
                host_asn_cache[item.key].append(value)

        self.assertEqual(data['asn_host_cache'], host_asn_cache)

        netblock_country_cache = {}
        for i, item in enumerate(mirrorlist.NetblockCountryCache):
            netblock_country_cache[
                IP(item.key)] = item.value

        self.assertEqual(
            data['netblock_country_cache'],
            netblock_country_cache)

        location_cache = {}
        for i, item in enumerate(mirrorlist.LocationCache):
            if item.key not in location_cache.keys():
                location_cache[item.key] = []
            for v, value in enumerate(item.value):
                location_cache[item.key].append(value)
        self.assertEqual(data['location_cache'], location_cache)

        hcurl_cache = {}
        for i, item in enumerate(mirrorlist.HCUrlCache):
            hcurl_cache[item.key] = item.value
        self.assertEqual(data['hcurl_cache'], hcurl_cache)

        file_details_cache = {}
        for i, item in enumerate(mirrorlist.FileDetailsCache):
            if item.directory not in file_details_cache.keys():
                file_details_cache[item.directory] = {}
            fdcf = item.FileDetailsCacheFiles
            for fd, file_details in enumerate(fdcf):
                file_details_cache[item.directory][file_details.filename] = []
                details_list = file_details.FileDetails
                for v, value in enumerate(details_list):
                    fd = {}
                    fd['timestamp'] = value.TimeStamp
                    fd['size'] = value.Size
                    fd['sha1'] = value.SHA1
                    fd['md5'] = value.MD5
                    fd['sha256'] = value.SHA256
                    fd['sha512'] = value.SHA512
                    file_details_cache[
                        item.directory][
                        file_details.filename].append(fd)

        self.assertEqual(data['file_details_cache'], file_details_cache)
        disabled_repositories = {}
        for i, item in enumerate(mirrorlist.DisabledRepositoryCache):
            disabled_repositories[item.key] = item.value
        self.assertEqual(data['disabled_repositories'], disabled_repositories)
        cou_con_redirect_cache = {}
        for i, item in enumerate(mirrorlist.CountryContinentRedirectCache):
            cou_con_redirect_cache[item.key] = item.value
        self.assertEqual(
            data['country_continent_redirect_cache'],
            cou_con_redirect_cache)
        repo_redirect_cache = {}
        for i, item in enumerate(mirrorlist.RepositoryRedirectCache):
            repo_redirect_cache[item.key] = item.value
        self.assertEqual(data['repo_redirect_cache'], repo_redirect_cache)

        repo_arch_to_directoryname = {}
        for i, item in enumerate(mirrorlist.RepoArchToDirectoryName):
            repo_arch_to_directoryname[
                (item.key.split('+')[0], item.key.split('+')[1])
            ] = item.value

        self.assertEqual(
            data['repo_arch_to_directoryname'],
            repo_arch_to_directoryname
        )

        host_max_connections_cache = {}
        for i, item in enumerate(mirrorlist.HostMaxConnectionCache):
            host_max_connections_cache[item.key] = item.value
        host_country_cache = {}
        for i, item in enumerate(mirrorlist.HostCountryCache):
            host_country_cache[item.key] = item.value
        host_bandwidth_cache = {}
        for i, item in enumerate(mirrorlist.HostBandwidthCache):
            host_bandwidth_cache[item.key] = item.value
        self.assertEqual(
            data['host_max_connections_cache'],
            host_max_connections_cache
        )
        self.assertEqual(
            data['host_country_cache'],
            host_country_cache
        )
        self.assertEqual(
            data['host_bandwidth_cache'],
            host_bandwidth_cache
        )

        host_netblock_cache = {}
        for i, item in enumerate(mirrorlist.HostNetblockCache):
            if IP(item.key) not in host_netblock_cache.keys():
                host_netblock_cache[IP(item.key)] = []
            for v, value in enumerate(item.value):
                host_netblock_cache[IP(item.key)].append(value)

        self.assertEqual(data['host_netblock_cache'], host_netblock_cache)

        mirrorlist_cache = {}
        for i, item in enumerate(mirrorlist.MirrorListCache):
            if item.directory not in mirrorlist_cache.keys():
                mirrorlist_cache[item.directory] = {}
            mc = mirrorlist_cache[item.directory]
            mc['subpath'] = item.Subpath
            mc['ordered_mirrorlist'] = item.OrderedMirrorList
            mc['global'] = set()
            for v, value in enumerate(item.Global):
                mc['global'].add(value)
            mc['byCountry'] = {}
            for c, country in enumerate(item.ByCountry):
                mc['byCountry'][country.key] = set()
                for v, value in enumerate(country.value):
                    mc['byCountry'][country.key].add(value)
            mc['byCountryInternet2'] = {}
            for c, country in enumerate(item.ByCountryInternet2):
                mc['byCountryInternet2'][country.key] = set()
                for v, value in enumerate(country.value):
                    mc['byCountryInternet2'][country.key].add(value)
            mc['byHostId'] = {}
            for i, id in enumerate(item.ByHostId):
                mc['byHostId'][id.key] = []
                for h, hcurl in enumerate(id.value):
                    mc['byHostId'][id.key].append(hcurl)

        self.assertEqual(data['mirrorlist_cache'], mirrorlist_cache)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MMLibtests)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
