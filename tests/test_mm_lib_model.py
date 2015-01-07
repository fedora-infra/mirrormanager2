# -*- coding: utf-8 -*-

'''
mirrormanager2 model tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MMLibModeltests)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
