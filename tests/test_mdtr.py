# -*- coding: utf-8 -*-

'''
mirrormanager2 tests for the `Move Devel To Release` (MDTL) script.
'''

from __future__ import print_function

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


class MDTLTest(tests.Modeltests):
    """ MDTL tests. """

    def setUp(self):
        """ Set up the environnment, ran before every test. """
        super(MDTLTest, self).setUp()

        self.configfile = os.path.join(
            FOLDER, 'mirrormanager2_tests_mdtr.cfg')
        with open(self.configfile, 'w') as stream:
            stream.write(CONFIG)

        self.script = os.path.join(
            FOLDER, '..', 'utility', 'mm2_move-devel-to-release')

        self.command = (
            '%s -c %s --version=27 --category=' %
            (self.script, self.configfile)).split()
        self.command[-1] += 'Fedora Linux'

        self.assertTrue(os.path.exists(self.configfile))

    def test_mdtr_no_data(self):
        """ Test the mdtr script without the appropriate data in the
        database.
        """
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
            "Category 'Fedora Linux' not found, exiting\n"
            "Available categories:\n")

        # Fill the DB a little bit
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(stdout, 'Version 27 not found for product Fedora\n')
        # Ignore for now
        #self.assertEqual(stderr, '')

        # One step further
        tests.create_version(self.session)

        process = subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(stdout, '')
        # Ignore for now
        #self.assertEqual(stderr, '')

    def test_mdtr(self):
        """ Test the mdtr script. """
        command = self.command[:]

        # Fill the DB a little bit
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)
        tests.create_version(self.session)

        item = model.Directory(
            name='pub/fedora/linux/releases/26/Everything/x86_64/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora/linux/releases/26/Everything/armhfp/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora-secondary/releases/26/Everything/ppc64le/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora-secondary/releases/26/Everything/sources/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora/linux/development/27/Everything/x86_64/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora/linux/releases/27/Everything/x86_64/os',
            readable=True,
        )
        self.session.add(item)

        item = model.Repository(
            name='pub/fedora/linux/development/27/Everything/x86_64/os',
            prefix='fedora-27',
            version_id=3,
            arch_id=3,
            directory_id=14,
            category_id=1,
        )
        self.session.add(item)
        item = model.Repository(
            name='pub/fedora/linux/releases/26/Everything/x86_64/os',
            prefix=None,
            version_id=1,
            arch_id=3,
            directory_id=10,
            category_id=1,
        )
        self.session.add(item)

        item = model.Category(
            name='Fedora Secondary Arches',
            product_id=2,
            canonicalhost='http://download.fedora.redhat.com',
            topdir_id=1,
            publiclist=True
        )
        self.session.add(item)

        self.session.commit()

        # Check before running the script

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 2)

        results = mirrormanager2.lib.get_directories(self.session)
        # create_directory creates 9 directories
        # we create 6 more here, 9+6=15
        self.assertEqual(len(results), 15)
        self.assertEqual(
            results[9].name,
            'pub/fedora/linux/releases/26/Everything/x86_64/os')
        self.assertEqual(
            results[10].name,
            'pub/fedora/linux/releases/26/Everything/armhfp/os')
        self.assertEqual(
            results[11].name,
            'pub/fedora-secondary/releases/26/Everything/ppc64le/os')
        self.assertEqual(
            results[12].name,
            'pub/fedora-secondary/releases/26/Everything/sources/os')
        self.assertEqual(
            results[13].name,
            'pub/fedora/linux/development/27/Everything/x86_64/os')
        self.assertEqual(
            results[14].name,
            'pub/fedora/linux/releases/27/Everything/x86_64/os')

        # Run the script

        process = subprocess.Popen(
            args=command[:],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(
            stdout,
            'pub/fedora/linux/development/27/Everything/x86_64/os '
            '=> pub/fedora/linux/releases/27/Everything/x86_64/os\n'
        )
        # Ignore for now
        #self.assertEqual(stderr, '')

        # Check after running the script

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 2)

        res = results[0]
        self.assertEqual(res.prefix, 'fedora-27')
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/27/Everything/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '27')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/27/Everything/x86_64/os')

        res = results[1]
        self.assertEqual(res.prefix, None)
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/26/Everything/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '26')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/26/Everything/x86_64/os')

        results = mirrormanager2.lib.get_directories(self.session)
        # create_directory creates 9 directories
        # we create 6 more here, 9+6=15
        self.assertEqual(len(results), 15)
        self.assertEqual(
            results[9].name,
            'pub/fedora/linux/releases/26/Everything/x86_64/os')
        self.assertEqual(
            results[10].name,
            'pub/fedora/linux/releases/26/Everything/armhfp/os')
        self.assertEqual(
            results[11].name,
            'pub/fedora-secondary/releases/26/Everything/ppc64le/os')
        self.assertEqual(
            results[12].name,
            'pub/fedora-secondary/releases/26/Everything/sources/os')
        self.assertEqual(
            results[13].name,
            'pub/fedora/linux/development/27/Everything/x86_64/os')
        self.assertEqual(
            results[14].name,
            'pub/fedora/linux/releases/27/Everything/x86_64/os')

        # Check non-existing version

        command = ('%s -c %s --version=24 '
                   '--category=' % (self.script, self.configfile)).split()
        command[-1] += 'Fedora Linux'

        process = subprocess.Popen(
            args=command[:],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(
            stdout,
            'Version 24 not found for product Fedora\n'
        )
        # Ignore for now
        #self.assertEqual(stderr, '')

        # Check after running the script

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 2)

        res = results[0]
        self.assertEqual(res.prefix, 'fedora-27')
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/27/Everything/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '27')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/27/Everything/x86_64/os')

        res = results[1]
        self.assertEqual(res.prefix, None)
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/26/Everything/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '26')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/26/Everything/x86_64/os')

        results = mirrormanager2.lib.get_directories(self.session)
        # create_directory creates 9 directories
        # we create 6 more here, 9+6=15
        self.assertEqual(len(results), 15)
        self.assertEqual(
            results[9].name,
            'pub/fedora/linux/releases/26/Everything/x86_64/os')
        self.assertEqual(
            results[10].name,
            'pub/fedora/linux/releases/26/Everything/armhfp/os')
        self.assertEqual(
            results[11].name,
            'pub/fedora-secondary/releases/26/Everything/ppc64le/os')
        self.assertEqual(
            results[12].name,
            'pub/fedora-secondary/releases/26/Everything/sources/os')
        self.assertEqual(
            results[13].name,
            'pub/fedora/linux/development/27/Everything/x86_64/os')
        self.assertEqual(
            results[14].name,
            'pub/fedora/linux/releases/27/Everything/x86_64/os')

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MDTLTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
