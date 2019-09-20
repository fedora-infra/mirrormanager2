# -*- coding: utf-8 -*-

'''
mirrormanager2 model tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os
import mirrormanager2.lib
import mirrormanager2.lib.model as model
import tests


class MMLibModeltests(tests.Modeltests):
    """ Model tests. """

    def test_mirrormanagerbasemixin(self):
        """ Test the MirrorManagerBaseMixin object of
        mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)

        item = model.Arch.get(self.session, 1)
        self.assertEqual(item.name, 'source')
        item = model.Arch.get(self.session, 3)
        self.assertEqual(item.name, 'x86_64')

    def test_site_repr(self):
        """ Test the Site.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_site(self.session)

        item = model.Site.get(self.session, 1)
        self.assertEqual(str(item), '<Site(1 - test-mirror)>')
        item = model.Site.get(self.session, 3)
        self.assertEqual(str(item), '<Site(3 - test-mirror_private)>')

    def test_host_repr(self):
        """ Test the Host.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_site(self.session)
        tests.create_hosts(self.session)

        item = model.Host.get(self.session, 1)
        self.assertEqual(str(item), '<Host(1 - mirror.localhost)>')
        item = model.Host.get(self.session, 3)
        self.assertEqual(str(item), '<Host(3 - private.localhost)>')

    def test_host_json(self):
        """ Test the Host.__json__ object of mirrormanager2.lib.model.
        """
        tests.create_site(self.session)
        tests.create_hosts(self.session)

        item = model.Host.get(self.session, 1)
        self.assertEqual(
            item.__json__(),
            {
                'admin_active': True,
                'asn': None,
                'asn_clients': False,
                'bandwidth_int': 100,
                'comment': None,
                'country': u'US',
                'id': 1,
                'internet2': False,
                'internet2_clients': False,
                'last_checked_in': None,
                'last_crawl_duration': 0,
                'last_crawled': None,
                'max_connections': 10,
                'name': u'mirror.localhost',
                'private': False,
                'site': {'id': 1, 'name': u'test-mirror'},
                'user_active': True
            }
        )
        item = model.Host.get(self.session, 3)
        self.assertEqual(
            item.__json__(),
            {
                'admin_active': True,
                'asn': None,
                'asn_clients': False,
                'bandwidth_int': 100,
                'comment': 'My own private mirror',
                'country': u'NL',
                'id': 3,
                'internet2': False,
                'internet2_clients': False,
                'last_checked_in': None,
                'last_crawl_duration': 0,
                'last_crawled': None,
                'max_connections': 10,
                'name': u'private.localhost',
                'private': True,
                'site': {'id': 1, 'name': u'test-mirror'},
                'user_active': True
            }
        )

    def test_host_set_not_up2date(self):
        """ Test the Host.set_not_up2date object of mirrormanager2.lib.model.
        """
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_hostcategory(self.session)
        tests.create_hostcategorydir(self.session)

        item = model.Host.get(self.session, 1)
        # Before change, all is up2date
        for hc in item.categories:
            for hcd in hc.directories:
                self.assertTrue(hcd.up2date)

        item.set_not_up2date(self.session)

        # After change, all is *not* up2date
        for hc in item.categories:
            for hcd in hc.directories:
                self.assertFalse(hcd.up2date)

    def test_host_is_active(self):
        """ Test the Host.is_active object of mirrormanager2.lib.model.
        """
        tests.create_site(self.session)
        tests.create_hosts(self.session)

        item = model.Host.get(self.session, 1)
        self.assertTrue(item.is_active())

        item.admin_active = False
        self.session.add(item)
        self.session.commit()

        item = model.Host.get(self.session, 1)
        self.assertFalse(item.is_active())

    def test_directory_repr(self):
        """ Test the Directory.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_directory(self.session)

        item = model.Directory.get(self.session, 1)
        self.assertEqual(
            str(item), '<Directory(1 - pub/fedora/linux)>')
        item = model.Directory.get(self.session, 3)
        self.assertEqual(str(item), '<Directory(3 - pub/epel)>')

    def test_product_repr(self):
        """ Test the Product.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)

        item = model.Product.get(self.session, 1)
        self.assertEqual(str(item), '<Product(1 - EPEL)>')
        item = model.Product.get(self.session, 2)
        self.assertEqual(str(item), '<Product(2 - Fedora)>')

    def test_product_displayed_versions(self):
        """ Test the Product.displayed_versions object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)

        item = model.Product.get(self.session, 1)
        self.assertEqual(item.displayed_versions, [])

        tests.create_version(self.session)

        item = model.Product.get(self.session, 1)
        self.assertEqual(item.displayed_versions[0].name, '7')

        item = model.Product.get(self.session, 2)
        for index, string in enumerate(['development', '27', '26', '25']):
            self.assertEqual(item.displayed_versions[index].name, string)

    def test_category_repr(self):
        """ Test the Category.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)

        item = model.Category.get(self.session, 1)
        self.assertEqual(str(item), '<Category(1 - Fedora Linux)>')
        item = model.Category.get(self.session, 2)
        self.assertEqual(str(item), '<Category(2 - Fedora EPEL)>')

    def test_hostcategory_repr(self):
        """ Test the HostCategory.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_site(self.session)
        tests.create_hosts(self.session)
        tests.create_hostcategory(self.session)

        item = model.HostCategory.get(self.session, 1)
        self.assertEqual(
            str(item), '<HostCategory(1 - <Category(1 - Fedora Linux)>)>')
        item = model.HostCategory.get(self.session, 2)
        self.assertEqual(
            str(item), '<HostCategory(2 - <Category(2 - Fedora EPEL)>)>')

    def test_categorydirectory_repr(self):
        """ Test the CategoryDirectory.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)

        item = mirrormanager2.lib.get_category_directory(self.session)
        self.assertEqual(str(item[0]), '<CategoryDirectory(1 - 1)>')
        self.assertEqual(str(item[1]), '<CategoryDirectory(2 - 3)>')

    def test_arch_repr(self):
        """ Test the Arch.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)

        item = model.Arch.get(self.session, 1)
        self.assertEqual(str(item), '<Arch(1 - source)>')
        item = model.Arch.get(self.session, 2)
        self.assertEqual(str(item), '<Arch(2 - i386)>')

    def test_version_repr(self):
        """ Test the Version.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_version(self.session)

        item = model.Version.get(self.session, 1)
        self.assertEqual(str(item), '<Version(1 - 26)>')
        item = model.Version.get(self.session, 2)
        self.assertEqual(str(item), '<Version(2 - 27-alpha)>')

    def test_version_arches(self):
        """ Test the Version.arches object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_version(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_repository(self.session)

        item = model.Version.get(self.session, 1)
        self.assertEqual(item.arches, set([u'x86_64']))
        item = model.Version.get(self.session, 2)
        self.assertEqual(item.arches, set([]))
        item = model.Version.get(self.session, 3)
        self.assertEqual(item.arches, set([u'x86_64']))

    def test_group_repr(self):
        """ Test the Group.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_user_groups(self.session)

        item = model.Group.get(self.session, 1)
        self.assertEqual(str(item), 'Group: 1 - name fpca')
        item = model.Group.get(self.session, 2)
        self.assertEqual(str(item), 'Group: 2 - name packager')

    def test_user_repr(self):
        """ Test the User.__repr__ object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_user_groups(self.session)

        item = model.User.get(self.session, 1)
        self.assertEqual(str(item), 'User: 1 - name pingou')
        item = model.User.get(self.session, 2)
        self.assertEqual(str(item), 'User: 2 - name kevin')
        item = model.User.get(self.session, 4)
        self.assertEqual(str(item), 'User: 4 - name shaiton')

    def test_user_username(self):
        """ Test the User.username object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_user_groups(self.session)

        for index, string in enumerate([
                'pingou', 'kevin', 'ralph', 'shaiton']):
            item = model.User.get(self.session, index + 1)
            self.assertEqual(item.username, string)

    def test_user_groups(self):
        """ Test the User.groups object of mirrormanager2.lib.model.
        """
        tests.create_base_items(self.session)
        tests.create_user_groups(self.session)

        item = model.User.get(self.session, 1)
        self.assertEqual(item.groups, ['fpca', 'packager'])
        item = model.User.get(self.session, 2)
        self.assertEqual(item.groups, ['fpca', 'packager'])
        item = model.User.get(self.session, 3)
        self.assertEqual(item.groups, ['fpca'])
        item = model.User.get(self.session, 4)
        self.assertEqual(item.groups, ['fpca', 'packager'])


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MMLibModeltests)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
