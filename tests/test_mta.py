# -*- coding: utf-8 -*-

'''
mirrormanager2 tests for the `Move To Archive` (MTA) script.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import subprocess
import sys
import os
import mirrormanager2.lib
import mirrormanager2.lib.model as model
import tests


FOLDER = os.path.dirname(os.path.abspath(__file__))

CONFIG = """
DB_URL = '%(db_path)s'


# Specify whether the crawler should send a report by email
CRAWLER_SEND_EMAIL =  False

""" % {'db_path': tests.DB_PATH}


class MTATest(tests.Modeltests):
    """ MTA tests. """

    def setUp(self):
        """ Set up the environnment, ran before every test. """
        super(MTATest, self).setUp()

        self.configfile = os.path.join(
            FOLDER, 'mirrormanager2_tests_mdtr.cfg')
        with open(self.configfile, 'w') as stream:
            stream.write(CONFIG)

        self.script = os.path.join(
            FOLDER, '..', 'utility', 'mm2_move-to-archive')

        self.command = ('%s -c %s --directoryRe=/26' % (
            self.script, self.configfile)).split()

        self.assertTrue(os.path.exists(self.configfile))

    def test_mta(self):
        """ Test the mta script. """
        command = self.command[:]

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        # Ignore for now
        #self.assertEqual(stderr, '')
        self.assertEqual(
            stdout,
            "No category could be found by the name: Fedora Linux\n")

        # Fill the DB a little bit
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)
        tests.create_version(self.session)
        tests.create_repository(self.session)

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(
            stdout,
            'No category could be found by the name: Fedora Archive\n')
        # Ignore for now
        #self.assertEqual(stderr, '')

        # One step further
        item = model.Directory(
            name='pub/archive',
            readable=True,
        )
        self.session.add(item)
        self.session.flush()
        item = model.Category(
            name='Fedora Archive',
            product_id=1,
            canonicalhost='http://archive.fedoraproject.org',
            topdir_id=10,
            publiclist=True
        )
        self.session.add(item)

        item = model.CategoryDirectory(
            directory_id=6,
            category_id=1,
        )
        self.session.add(item)
        item = model.CategoryDirectory(
            directory_id=8,
            category_id=1,
        )
        self.session.add(item)

        self.session.commit()

        # Before the script

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].prefix, 'updates-testing-f25')
        self.assertEqual(
            results[0].directory.name,
            'pub/fedora/linux/updates/testing/25/x86_64')
        self.assertEqual(results[1].prefix, 'updates-testing-f26')
        self.assertEqual(
            results[1].directory.name,
            'pub/fedora/linux/updates/testing/26/x86_64')
        self.assertEqual(results[2].prefix, 'updates-testing-f27')
        self.assertEqual(
            results[2].directory.name,
            'pub/fedora/linux/updates/testing/27/x86_64')

        results = mirrormanager2.lib.get_directories(self.session)
        # create_directory creates 9 directories
        # we create 1 more here, 9+1=10
        self.assertEqual(len(results), 10)
        self.assertEqual(results[0].name, 'pub/fedora/linux')
        self.assertEqual(results[1].name, 'pub/fedora/linux/extras')
        self.assertEqual(results[2].name, 'pub/epel')
        self.assertEqual(results[3].name, 'pub/fedora/linux/releases/26')
        self.assertEqual(results[4].name, 'pub/fedora/linux/releases/27')
        self.assertEqual(
            results[5].name,
            'pub/archive/fedora/linux/releases/26/Everything/source')
        self.assertEqual(
            results[6].name,
            'pub/fedora/linux/updates/testing/25/x86_64')
        self.assertEqual(
            results[7].name,
            'pub/fedora/linux/updates/testing/26/x86_64')
        self.assertEqual(
            results[8].name,
            'pub/fedora/linux/updates/testing/27/x86_64')
        self.assertEqual(results[9].name, 'pub/archive')

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(
            stdout,
            'trying to find pub/archive/fedora/linux/updates/testing/'
            '26/x86_64\n'
            'Unable to find a directory in [Fedora Archive] for pub/fedora/'
            'linux/updates/testing/26/x86_64\n')
        # Ignore for now
        #self.assertEqual(stderr, '')

        # Run the script so that it works

        item = model.Directory(
            name='pub/archive/fedora/linux/updates/testing/26/x86_64',
            readable=True,
        )
        self.session.add(item)
        self.session.commit()

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(
            stdout,
            'trying to find pub/archive/fedora/'
            'linux/updates/testing/26/x86_64\n'
            'pub/fedora/linux/updates/testing/26/x86_64 => '
            'pub/archive/fedora/linux/updates/testing/26/x86_64\n')
        # Ignore for now
        #self.assertEqual(stderr, '')

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].prefix, 'updates-testing-f25')
        self.assertEqual(
            results[0].directory.name,
            'pub/fedora/linux/updates/testing/25/x86_64')
        self.assertEqual(results[1].prefix, 'updates-testing-f26')
        self.assertEqual(
            results[1].directory.name,
            'pub/archive/fedora/linux/updates/testing/26/x86_64')
        self.assertEqual(results[2].prefix, 'updates-testing-f27')
        self.assertEqual(
            results[2].directory.name,
            'pub/fedora/linux/updates/testing/27/x86_64')

        # After the script

        results = mirrormanager2.lib.get_directories(self.session)
        # create_directory creates 9 directories
        # we create 1 more here, 9+1=10
        self.assertEqual(len(results), 11)
        self.assertEqual(results[0].name, 'pub/fedora/linux')
        self.assertEqual(results[1].name, 'pub/fedora/linux/extras')
        self.assertEqual(results[2].name, 'pub/epel')
        self.assertEqual(results[3].name, 'pub/fedora/linux/releases/26')
        self.assertEqual(results[4].name, 'pub/fedora/linux/releases/27')
        self.assertEqual(
            results[5].name,
            'pub/archive/fedora/linux/releases/26/Everything/source')
        self.assertEqual(
            results[6].name,
            'pub/fedora/linux/updates/testing/25/x86_64')
        self.assertEqual(
            results[7].name,
            'pub/fedora/linux/updates/testing/26/x86_64')
        self.assertEqual(
            results[8].name,
            'pub/fedora/linux/updates/testing/27/x86_64')
        self.assertEqual(results[9].name, 'pub/archive')
        self.assertEqual(
            results[10].name,
            'pub/archive/fedora/linux/updates/testing/26/x86_64')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MTATest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
