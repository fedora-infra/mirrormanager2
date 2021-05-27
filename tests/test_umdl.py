# -*- coding: utf-8 -*-

'''
mirrormanager2 tests for the `Update Master Directory List` (UMDL) cron.
'''

from __future__ import print_function

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources
import unittest
import subprocess
import sys
import os
import mirrormanager2.lib
import tests


FOLDER = os.path.dirname(os.path.abspath(__file__))

CONFIG = """
DB_URL = '%(db_path)s'
UMDL_PREFIX = '%(folder)s/../testdata/'

# Specify whether the crawler should send a report by email
CRAWLER_SEND_EMAIL =  False

umdl_master_directories = [
    {
        'type': 'directory',
        'path': '%(folder)s/../testdata/pub/epel/',
        'category': 'Fedora EPEL'
    },
    {
        'type': 'directory',
        'path': '%(folder)s/../testdata/pub/fedora/linux/',
        'category': 'Fedora Linux'
    },
    {
        'type': 'directory',
        'path': '%(folder)s/../testdata/pub/fedora-secondary/',
        'category': 'Fedora Secondary Arches'
    },
    {
        'type': 'directory',
        'path': '%(folder)s/../testdata/pub/archive/',
        'category': 'Fedora Archive'
    },
    {
        'type': 'directory',
        'path': '%(folder)s/../testdata/pub/alt/',
        'category': 'Fedora Other'
    }
]
""" % {'db_path': tests.DB_PATH, 'folder': FOLDER}


class UMDLTest(tests.Modeltests):
    """ UMDL tests. """

    def setUp(self):
        """ Set up the environnment, ran before every test. """
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

        process = subprocess.Popen(
            args=self.umdl_command.split(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(stdout, '')
        # Ignore for now
        #self.assertEqual(stderr, '')

        with open(self.logfile) as stream:
            logs = stream.readlines()
        logs = ''.join([
            log.split(':', 3)[-1]
            for log in logs
        ])
        print(logs)
        exp = """N/A:Starting umdl
Fedora EPEL:umdl_master_directories Category Fedora EPEL does not exist in the database, skipping
Fedora Linux:umdl_master_directories Category Fedora Linux does not exist in the database, skipping
Fedora Secondary Arches:umdl_master_directories Category Fedora Secondary Arches does not exist in the database, skipping
Fedora Archive:umdl_master_directories Category Fedora Archive does not exist in the database, skipping
Fedora Other:umdl_master_directories Category Fedora Other does not exist in the database, skipping
Fedora Other:Refresh the list of repomd.xml
Fedora Other:Ending umdl
"""
        self.assertEqual(logs, exp)

    def test_1_umdl(self):
        """ Test the umdl cron. """

        # Fill the DB a little bit
        tests.create_base_items(self.session)
        tests.create_directory(self.session)
        tests.create_category(self.session)
        tests.create_categorydirectory(self.session)

        # Run the UDML

        process = subprocess.Popen(
            args=self.umdl_command.split(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()

        self.assertEqual(stdout, '')
        # Ignore for now
        #self.assertEqual(stderr, '')

        with open(self.logfile) as stream:
            logs = stream.readlines()
        logs = ''.join([
            log.split(':', 3)[-1]
            for log in logs
        ])

        for i in [
                'N/A:Starting umdl',
                'Fedora Linux: has changed: 0 !=',
                'Fedora Linux:development has changed: 0 !=',
                'Fedora Linux:releases/20/Fedora has changed: 0 !=',
                'Fedora/source/SRPMS/r has changed: 0 !=',
                'releases/20/Fedora/x86_64/iso has changed: 0 !=',
                'releases/20/Live/x86_64 has changed: 0 !=',
                'Fedora Linux:Updating FileDetail <mirrormanager2.lib.model',
                'Created Version(product=<Product(2 - Fedora)>',
                'Version(product=<Product(2 - Fedora)>, name=20',
                'Repository(prefix=None, version=20, arch=source',
                'ategory Fedora Secondary Arches does not exist',
                'Fedora Other:Refresh the list of repomd.xml'
        ]:
            self.assertTrue(i in logs)

        # The DB should now be filled with what UMDL added, so let's check it
        results = mirrormanager2.lib.query_directories(self.session)
        self.assertEqual(len(results), 0)

        results = mirrormanager2.lib.get_versions(self.session)
        self.assertEqual(len(results), 2)
        for result in results:
            version_names = [ '22', '20' ]
            self.assertTrue(result.name in version_names)
            if result.name == '22':
                self.assertEqual(result.product.name, 'Fedora')
            if result.name == '20':
                self.assertEqual(result.product.name, 'Fedora')

        results = mirrormanager2.lib.get_categories(self.session)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'Fedora Linux')
        self.assertEqual(results[1].name, 'Fedora EPEL')

        results = mirrormanager2.lib.get_products(self.session)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'EPEL')
        self.assertEqual(results[1].name, 'Fedora')

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 3)
        check_counter = 0
        for result in results:
            if result.name == 'pub/fedora/linux/development/22/x86_64/os':
                self.assertEqual(result.category.name, 'Fedora Linux')
                self.assertEqual(result.version.name, '22')
                self.assertEqual(result.arch.name, 'x86_64')
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/development/22/x86_64/os')
                self.assertEqual(result.prefix, None)
                check_counter += 1
            if result.name == 'pub/fedora/linux/releases/20/Fedora/x86_64/os':
                self.assertEqual(result.category.name, 'Fedora Linux')
                self.assertEqual(result.version.name, '20')
                self.assertEqual(result.arch.name, 'x86_64')
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/releases/20/Fedora/x86_64/os')
                self.assertEqual(result.prefix, 'fedora-install-20')
                check_counter += 1

        self.assertEqual(check_counter, 2)

        results = mirrormanager2.lib.get_arches(self.session)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].name, 'i386')
        self.assertEqual(results[1].name, 'ppc')
        self.assertEqual(results[2].name, 'source')
        self.assertEqual(results[3].name, 'x86_64')

        results = mirrormanager2.lib.get_directories(self.session)
        # tree testdata/pub says there are 49 directories and 49 files
        # There are 7 directories added by create_directory which are not
        # present on the FS, 49 + 7 = 56, so we are good \ó/
        self.assertEqual(len(results), 56)
        self.assertEqual(results[0].name, 'pub/fedora/linux')
        self.assertEqual(results[1].name, 'pub/fedora/linux/extras')
        self.assertEqual(results[2].name, 'pub/epel')
        self.assertEqual(results[3].name, 'pub/fedora/linux/releases/26')
        self.assertEqual(results[4].name, 'pub/fedora/linux/releases/27')
        self.assertEqual(
            results[5].name,
            'pub/archive/fedora/linux/releases/26/Everything/source')
        self.assertEqual(
            results[20].name,
            'pub/fedora/linux/releases/20/Fedora/source/SRPMS/b')

        results = mirrormanager2.lib.get_file_detail(
            self.session, 'repomd.xml', 7)
        self.assertEqual(results, None)

        results = mirrormanager2.lib.get_file_details(self.session)
        self.assertEqual(len(results), 7)

        check_counter = 0
        for result in results:
            if result.filename == 'Fedora-20-x86_64-DVD.iso':
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/releases/20/Fedora/x86_64/iso')
                self.assertEqual(result.sha512, None)
                self.assertEqual(
                    result.sha256,
                    'f2eeed5102b8890e9e6f4b9053717fe73031e699c4b76dc7028749ab66e7f917')
                check_counter += 1

            elif result.filename == 'Fedora-20-x86_64-netinst.iso':
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/releases/20/Fedora/x86_64/iso')
                self.assertEqual(result.sha512, None)
                self.assertEqual(
                    result.sha256,
                    '376be7d4855ad6281cb139430606a782fd6189dcb01d7b61448e915802cc350f')
                check_counter += 1

            elif result.filename == 'Fedora-Live-Desktop-x86_64-20-1.iso':
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/releases/20/Live/x86_64')
                self.assertEqual(result.sha512, None)
                self.assertEqual(
                    result.sha256,
                    'cc0333be93c7ff2fb3148cb29360d2453f78913cc8aa6c6289ae6823372a77d2')
                check_counter += 1

            elif result.filename == 'Fedora-Live-KDE-x86_64-20-1.iso':
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/releases/20/Live/x86_64')
                self.assertEqual(result.sha512, None)
                self.assertEqual(
                    result.sha256,
                    '08360a253b4a40dff948e568dba1d2ae9d931797f57aa08576b8b9f1ef7e4745')
                check_counter += 1

            elif result.md5 == 'd0fb87891c3bfbdaf7a225f57e9ba6ee':
                self.assertEqual(result.filename, 'repomd.xml')
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/development/22/x86_64/os/repodata')
                self.assertEqual(
                    result.sha256,
                    '860f0f832f7a641cf8f7e27172ef9b2492ce849388e43f372af7e512aa646677')
                self.assertEqual(
                    result.sha512,
                    '7bb9a0bae076ccbbcd086163a1d4f33b62321aa6991d135c42bf3f6c42c4eb'
                    '465a0b42c62efa809708543fcd69511cb19cd7111d5ff295a50253b9c7659b'
                    'b9d6')
                check_counter += 1

            elif result.md5 == '082970dfa804fdcfaed2e15e2e5fba7d':
                self.assertEqual(result.filename, 'repomd.xml')
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/releases/20/Fedora/source/SRPMS/repodata')
                self.assertEqual(
                    result.sha256,
                    '9a4738934092cf17e4540ee9cab741e922eb8306875ae5621feb01ebeb1f67f2')
                self.assertEqual(
                    result.sha512,
                    '3351c7a6b1d2bd94e375d09324a9280b8becfe4dea40a227c3b270ddcedb19'
                    'f420eec3f2c6a39a1edcdf52f80d31eb47a0ba25057ced2e3182dd212bc746'
                    '6ba2')
                check_counter += 1

            elif result.md5 == '49db42c616518f465014c3605de4414d':
                self.assertEqual(result.filename, 'repomd.xml')
                self.assertEqual(
                    result.directory.name,
                    'pub/fedora/linux/releases/20/Fedora/x86_64/os/repodata')
                self.assertEqual(
                    result.sha256,
                    '108b4102829c0839c7712832577fe7da24f0a9491f4dc25d4145efe6aced2ebf')
                self.assertEqual(
                    result.sha512,
                    '50ed8cb8f4daf8bcd1d0ccee1710b8a87ee8de5861fb15a1023d6558328795'
                    'f42dade3e025c09c20ade36c77a3a82d9cdce1a2e2ad171f9974bc1889b591'
                    '8020')
                check_counter += 1

        self.assertEqual(check_counter, 7)

        results = mirrormanager2.lib.get_host_category_dirs(self.session)
        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(UMDLTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
