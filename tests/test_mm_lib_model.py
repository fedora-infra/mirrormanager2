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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MMLibModeltests)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
