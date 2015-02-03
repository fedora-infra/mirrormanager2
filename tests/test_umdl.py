# -*- coding: utf-8 -*-

'''
mirrormanager2 tests for the `Update Master Directory List` (UMDL) cron.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import subprocess
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import mirrormanager2.lib
import tests


FOLDER = os.path.dirname(os.path.abspath(__file__))

CONFIG = """
DB_URL = '%s'


# Specify whether the crawler should send a report by email
CRAWLER_SEND_EMAIL =  False

umdl_master_directories = [
    {
        'type': 'directory',
        'path': '../testdata/pub/epel/',
        'category': 'Fedora EPEL'
    },
    {
        'type': 'directory',
        'path': '../testdata/pub/fedora/linux/',
        'category': 'Fedora Linux'
    },
    {
        'type': 'directory',
        'path': '../testdata/pub/fedora-secondary/',
        'category': 'Fedora Secondary Arches'
    },
    {
        'type': 'directory',
        'path': '../testdata/pub/archive/',
        'category': 'Fedora Archive'
    },
    {
        'type': 'directory',
        'path': '../testdata/pub/alt/',
        'category': 'Fedora Other'
    }
]
""" % tests.DB_PATH


class UMDLTest(tests.Modeltests):
    """ UMDL tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(UMDLTest, self).setUp()

        self.logfile = os.path.join(FOLDER, 'umdl.log')
        if os.path.exists(self.logfile):
            os.unlink(self.logfile)

        self.configfile = os.path.join(FOLDER, 'mirrormanager2_tests.cfg')
        with open(self.configfile, 'w') as stream:
            stream.write(CONFIG)

        self.umdlscript = os.path.join(
            FOLDER, '..', 'utility', 'mm2_update-master-directory-list')

        self.umdl_command = '%s -c %s --logfile=%s' % (
            self.umdlscript, self.configfile, self.logfile)

        self.assertTrue(os.path.exists(self.configfile))
        self.assertFalse(os.path.exists(self.logfile))

    def test_0_umdl_empty_db(self):
        """ Test the umdl cron against an empty database. """

        process = subprocess.Popen(args=self.umdl_command.split())
        stdout, stderr = process.communicate()

        self.assertEqual(stdout, None)
        self.assertEqual(stderr, None)

        with open(self.logfile) as stream:
            logs = stream.readlines()
        self.assertEqual(len(logs), 5)
        logs = ''.join([
            log.split(' ', 3)[-1]
            for log in logs
        ])
        exp ="""umdl_master_directories Category Fedora EPEL does not exist in the database, skipping
umdl_master_directories Category Fedora Linux does not exist in the database, skipping
umdl_master_directories Category Fedora Secondary Arches does not exist in the database, skipping
umdl_master_directories Category Fedora Archive does not exist in the database, skipping
umdl_master_directories Category Fedora Other does not exist in the database, skipping
"""
        self.assertEqual(logs, exp)

    def test_1_umdl(self):
        """ Test the umdl cron. """

        # Fill the DB a little bit
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)

        process = subprocess.Popen(args=self.umdl_command.split())
        stdout, stderr = process.communicate()

        self.assertEqual(stdout, None)
        self.assertEqual(stderr, None)

        with open(self.logfile) as stream:
            logs = stream.readlines()
        self.assertEqual(len(logs), 3)
        logs = ''.join([
            log.split(' ', 3)[-1]
            for log in logs
        ])
        exp ="""umdl_master_directories Category Fedora Secondary Arches does not exist in the database, skipping
umdl_master_directories Category Fedora Archive does not exist in the database, skipping
umdl_master_directories Category Fedora Other does not exist in the database, skipping
"""
        self.assertEqual(logs, exp)

        # The DB should now be filled with what UMDL added, so let's check it
        results = mirrormanager2.lib.query_directories(self.session)
        self.assertEqual(len(results), 0)

        results = mirrormanager2.lib.get_versions(self.session)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, '21')
        self.assertEqual(results[0].product.name, 'Fedora')

        results = mirrormanager2.lib.get_categories(self.session)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'Fedora Linux')
        self.assertEqual(results[1].name, 'Fedora EPEL')

        results = mirrormanager2.lib.get_products(self.session)
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0].name, 'EPEL')
        self.assertEqual(
            results[1].name, 'Fedora')

        results = sorted(mirrormanager2.lib.get_repositories(self.session))
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].name, 'pub/fedora/linux/releases/atomic/21')
        self.assertEqual(results[0].category.name, 'Fedora Linux')
        self.assertEqual(results[0].version.name, '21')
        self.assertEqual(results[0].arch.name, 'x86_64')
        self.assertEqual(
            results[0].directory.name, 'pub/fedora/linux/releases/atomic/21')

        results = mirrormanager2.lib.get_arches(self.session)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].name, 'i386')
        self.assertEqual(results[1].name, 'ppc')
        self.assertEqual(results[2].name, 'source')
        self.assertEqual(results[3].name, 'x86_64')

        results = mirrormanager2.lib.get_directories(self.session)
        self.assertEqual(len(results), 61)
        self.assertEqual(results[0].name, 'pub/fedora/linux/releases')
        self.assertEqual(results[1].name, 'pub/fedora/linux/extras')
        self.assertEqual(results[2].name, 'pub/epel')
        self.assertEqual(results[3].name, 'pub/fedora/linux/releases/20')
        self.assertEqual(results[4].name, 'pub/fedora/linux/releases/21')
        self.assertEqual(
            results[5].name,
            'pub/archive/fedora/linux/releases/20/Fedora/source')
        self.assertEqual(
            results[20].name,
            'pub/fedora/linux/releases/atomic/21/refs/heads/fedora-atomic/f21')
        self.assertEqual(
            results[21].name,
            'pub/fedora/linux/releases/atomic/21/refs/heads/'
            'fedora-atomic/f21/x86_64')
        self.assertEqual(
            results[22].name,
            'pub/fedora/linux/releases/atomic/21/refs/heads/'
            'fedora-atomic/f21/x86_64/updates')
        self.assertEqual(
            results[23].name,
            'pub/fedora/linux/releases/atomic/21/refs/remotes')
        self.assertEqual(
            results[24].name,
            'pub/fedora/linux/releases/atomic/21/remote-cache')

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7)
        self.assertEqual(results, None)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(UMDLTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
