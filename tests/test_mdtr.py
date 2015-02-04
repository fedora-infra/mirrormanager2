# -*- coding: utf-8 -*-

'''
mirrormanager2 tests for the `Move Devel To Release` (MDTL) script.
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
import mirrormanager2.lib.model as model
import tests


FOLDER = os.path.dirname(os.path.abspath(__file__))

CONFIG = """
DB_URL = '%(db_path)s'


# Specify whether the crawler should send a report by email
CRAWLER_SEND_EMAIL =  False

""" % {'db_path': tests.DB_PATH}


class MDTLTest(tests.Modeltests):
    """ MDTL tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(MDTLTest, self).setUp()

        self.configfile = os.path.join(
            FOLDER, 'mirrormanager2_tests_mdtr.cfg')
        with open(self.configfile, 'w') as stream:
            stream.write(CONFIG)

        self.script = os.path.join(
            FOLDER, '..', 'utility', 'mm2_move-devel-to-release')

        self.command = ('%s -c %s --version=20 '\
            '--category=' % (self.script, self.configfile)).split()
        self.command[-1] += 'Fedora Linux'

        self.assertTrue(os.path.exists(self.configfile))

    def test_mdtr_no_data(self):
        """ Test the mdtr script without the appropriate data in the
        database.
        """
        command = self.command[:]

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        self.assertEqual(stderr, '')
        self.assertEqual(
            stdout,
            "Category 'Fedora Linux' not found, exiting\n"
            "Available categories:\n")

        # Fill the DB a little bit
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        self.assertEqual(stdout, 'Version 20 not found for product Fedora\n')
        self.assertEqual(stderr, '')

        # One step further
        tests.create_version(self.session)

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        self.assertEqual(stdout,
            'directory pub/fedora/linux/releases/20/Fedora/i386/os does not '
            'exist on disk, skipping creation of a repository there\n'
            'directory pub/fedora-secondary/releases/20/Fedora/ppc/os does '
            'not exist on disk, skipping creation of a repository there\n'
            'directory pub/fedora/linux/releases/20/Fedora/x86_64/os does '
            'not exist on disk, skipping creation of a repository there\n')
        self.assertEqual(stderr, '')

        process = subprocess.Popen(
            args=command[:] + ['--test'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        self.assertEqual(stdout,
            'directory pub/fedora/linux/releases/20/Fedora/i386/os exists on'
            ' disk, but not in the database yet, skipping creation of a '
            'repository there until after the next UMDL run.\n'
            'directory pub/fedora-secondary/releases/20/Fedora/ppc/os exists '
            'on disk, but not in the database yet, skipping creation of a '
            'repository there until after the next UMDL run.\n'
            'directory pub/fedora/linux/releases/20/Fedora/x86_64/os exists '
            'on disk, but not in the database yet, skipping creation of a '
            'repository there until after the next UMDL run.\n')
        self.assertEqual(stderr, '')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MDTLTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
