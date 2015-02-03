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

from mirrormanager2.lib import model
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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(UMDLTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
