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
        """ Set up the environnment, ran before every test. """
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
            name='pub/fedora/linux/releases/20/Fedora/x86_64/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora/linux/releases/20/Fedora/i386/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora-secondary/releases/20/Fedora/ppc/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora-secondary/releases/20/Fedora/sources/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora/linux/development/21/x86_64/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora/linux/releases/21/Fedora/x86_64/os',
            readable=True,
        )
        self.session.add(item)
        item = model.Directory(
            name='pub/fedora/linux/releases/21/Everything/x86_64/os',
            readable=True,
        )
        self.session.add(item)

        item = model.Repository(
            name='pub/fedora/linux/development/21/x86_64/os',
            prefix='fedora-21',
            version_id=3,
            arch_id=3,
            directory_id=14,
            category_id=1,
        )
        self.session.add(item)
        item = model.Repository(
            name='pub/fedora/linux/releases/21/Everything/x86_64/os',
            prefix=None,
            version_id=3,
            arch_id=3,
            directory_id=16,
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
        # we create 7 more here, 9+7=16
        self.assertEqual(len(results), 16)
        self.assertEqual(
            results[9].name,
            'pub/fedora/linux/releases/20/Fedora/x86_64/os')
        self.assertEqual(
            results[10].name,
            'pub/fedora/linux/releases/20/Fedora/i386/os')
        self.assertEqual(
            results[11].name,
            'pub/fedora-secondary/releases/20/Fedora/ppc/os')
        self.assertEqual(
            results[12].name,
            'pub/fedora-secondary/releases/20/Fedora/sources/os')
        self.assertEqual(
            results[13].name,
            'pub/fedora/linux/development/21/x86_64/os')
        self.assertEqual(
            results[14].name,
            'pub/fedora/linux/releases/21/Fedora/x86_64/os')
        self.assertEqual(
            results[15].name,
            'pub/fedora/linux/releases/21/Everything/x86_64/os')

        # Run the script

        process = subprocess.Popen(
            args=command[:] + ['--test'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        self.assertEqual(
            stdout,
            'updating fedora-install-20 repo for arch i386\n'
            'updating fedora-install-20 repo for arch ppc\n'
            'updating fedora-install-20 repo for arch x86_64\n'
        )
        self.assertEqual(stderr, '')

        # Check after running the script

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 5)

        res = results[0]
        self.assertEqual(res.prefix, 'fedora-21')
        self.assertEqual(
            res.name, 'pub/fedora/linux/development/21/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '21')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/development/21/x86_64/os')

        res = results[1]
        self.assertEqual(res.prefix, None)
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/21/Everything/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '21')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/21/Everything/x86_64/os')

        res = results[2]
        self.assertEqual(res.prefix, 'fedora-install-20')
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/20/Fedora/i386/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '20')
        self.assertEqual(res.arch.name, 'i386')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/20/Fedora/i386/os')

        res = results[3]
        self.assertEqual(res.prefix, 'fedora-install-20')
        self.assertEqual(
            res.name, 'pub/fedora-secondary/releases/20/Fedora/ppc/os')
        self.assertEqual(res.category.name, 'Fedora Secondary Arches')
        self.assertEqual(res.version.name, '20')
        self.assertEqual(res.arch.name, 'ppc')
        self.assertEqual(
            res.directory.name,
            'pub/fedora-secondary/releases/20/Fedora/ppc/os')

        res = results[4]
        self.assertEqual(res.prefix, 'fedora-install-20')
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/20/Fedora/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '20')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/20/Fedora/x86_64/os')

        results = mirrormanager2.lib.get_directories(self.session)
        # create_directory creates 9 directories
        # we create 7 more here, 9+7=16
        self.assertEqual(len(results), 16)
        self.assertEqual(
            results[9].name,
            'pub/fedora/linux/releases/20/Fedora/x86_64/os')
        self.assertEqual(
            results[10].name,
            'pub/fedora/linux/releases/20/Fedora/i386/os')
        self.assertEqual(
            results[11].name,
            'pub/fedora-secondary/releases/20/Fedora/ppc/os')
        self.assertEqual(
            results[12].name,
            'pub/fedora-secondary/releases/20/Fedora/sources/os')
        self.assertEqual(
            results[13].name,
            'pub/fedora/linux/development/21/x86_64/os')
        self.assertEqual(
            results[14].name,
            'pub/fedora/linux/releases/21/Fedora/x86_64/os')
        self.assertEqual(
            results[15].name,
            'pub/fedora/linux/releases/21/Everything/x86_64/os')

        # Update F21

        command = ('%s -c %s --version=21 '\
            '--category=' % (self.script, self.configfile)).split()
        command[-1] += 'Fedora Linux'

        process = subprocess.Popen(
            args=command[:] + ['--test'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        print stdout

        self.assertEqual(
            stdout,
            'pub/fedora/linux/development/21/x86_64/os => '
            'pub/fedora/linux/releases/21/Everything/x86_64/os\n'
            'directory pub/fedora/linux/releases/21/Fedora/i386/os exists '
            'on disk, but not in the database yet, skipping creation of a '
            'repository there until after the next UMDL run.\n'
            'directory pub/fedora-secondary/releases/21/Fedora/ppc/os exists '
            'on disk, but not in the database yet, skipping creation of a '
            'repository there until after the next UMDL run.\n'
            'updating fedora-install-21 repo for arch x86_64\n'
        )
        self.assertEqual(stderr, '')

        # Check after running the script

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 6)

        res = results[0]
        self.assertEqual(res.prefix, 'fedora-21')
        self.assertEqual(
            res.name, 'pub/fedora/linux/development/21/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '21')
        self.assertEqual(res.arch, None)
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/development/21/x86_64/os')

        res = results[1]
        self.assertEqual(res.prefix, 'fedora-21')
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/21/Everything/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '21')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/21/Everything/x86_64/os')

        res = results[2]
        self.assertEqual(res.prefix, 'fedora-install-20')
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/20/Fedora/i386/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '20')
        self.assertEqual(res.arch.name, 'i386')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/20/Fedora/i386/os')

        res = results[3]
        self.assertEqual(res.prefix, 'fedora-install-20')
        self.assertEqual(
            res.name, 'pub/fedora-secondary/releases/20/Fedora/ppc/os')
        self.assertEqual(res.category.name, 'Fedora Secondary Arches')
        self.assertEqual(res.version.name, '20')
        self.assertEqual(res.arch.name, 'ppc')
        self.assertEqual(
            res.directory.name,
            'pub/fedora-secondary/releases/20/Fedora/ppc/os')

        res = results[4]
        self.assertEqual(res.prefix, 'fedora-install-20')
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/20/Fedora/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '20')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/20/Fedora/x86_64/os')

        res = results[5]
        self.assertEqual(res.prefix, 'fedora-install-21')
        self.assertEqual(
            res.name, 'pub/fedora/linux/releases/21/Fedora/x86_64/os')
        self.assertEqual(res.category.name, 'Fedora Linux')
        self.assertEqual(res.version.name, '21')
        self.assertEqual(res.arch.name, 'x86_64')
        self.assertEqual(
            res.directory.name,
            'pub/fedora/linux/releases/21/Fedora/x86_64/os')

        results = mirrormanager2.lib.get_directories(self.session)
        # create_directory creates 9 directories
        # we create 7 more here, 9+7=16
        self.assertEqual(len(results), 16)
        self.assertEqual(
            results[9].name,
            'pub/fedora/linux/releases/20/Fedora/x86_64/os')
        self.assertEqual(
            results[10].name,
            'pub/fedora/linux/releases/20/Fedora/i386/os')
        self.assertEqual(
            results[11].name,
            'pub/fedora-secondary/releases/20/Fedora/ppc/os')
        self.assertEqual(
            results[12].name,
            'pub/fedora-secondary/releases/20/Fedora/sources/os')
        self.assertEqual(
            results[13].name,
            'pub/fedora/linux/development/21/x86_64/os')
        self.assertEqual(
            results[14].name,
            'pub/fedora/linux/releases/21/Fedora/x86_64/os')
        self.assertEqual(
            results[15].name,
            'pub/fedora/linux/releases/21/Everything/x86_64/os')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(MDTLTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
