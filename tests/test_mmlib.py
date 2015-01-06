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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MMLibtests)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
