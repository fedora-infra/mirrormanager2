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
DB_URL = '%(db_path)s'


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
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, 'development')
        self.assertEqual(results[0].product.name, 'Fedora')
        self.assertEqual(results[1].name, '21')
        self.assertEqual(results[1].product.name, 'Fedora')

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

        results = mirrormanager2.lib.get_repositories(self.session)
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0].name, 'pub/fedora/linux/releases/atomic/rawhide')
        self.assertEqual(results[0].category.name, 'Fedora Linux')
        self.assertEqual(results[0].version.name, 'development')
        self.assertEqual(results[0].arch.name, 'x86_64')
        self.assertEqual(
            results[0].directory.name,
            'pub/fedora/linux/releases/atomic/rawhide')
        self.assertEqual(
            results[1].name, 'pub/fedora/linux/releases/atomic/21')
        self.assertEqual(results[1].category.name, 'Fedora Linux')
        self.assertEqual(results[1].version.name, '21')
        self.assertEqual(results[1].arch.name, 'x86_64')
        self.assertEqual(
            results[1].directory.name, 'pub/fedora/linux/releases/atomic/21')

        results = mirrormanager2.lib.get_arches(self.session)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].name, 'i386')
        self.assertEqual(results[1].name, 'ppc')
        self.assertEqual(results[2].name, 'source')
        self.assertEqual(results[3].name, 'x86_64')

        results = mirrormanager2.lib.get_directories(self.session)
        # tree testdata/pub says there are 79 directories and 136 files
        # There are 7 directories added by create_directory which are not
        # present on the FS, 79 + 7 = 86, so we are good \ó/
        self.assertEqual(len(results), 86)
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

        results = mirrormanager2.lib.get_file_details(self.session)
        self.assertEqual(len(results), 8)

        self.assertEqual(results[0].filename, 'Fedora-20-x86_64-DVD.iso')
        self.assertEqual(
            results[0].directory.name,
            'pub/fedora/linux/releases/releases/20/Fedora/x86_64/iso')
        self.assertEqual(results[0].sha512, None)
        self.assertEqual(
            results[0].sha256,
            'f2eeed5102b8890e9e6f4b9053717fe73031e699c4b76dc7028749ab66e7f917')

        self.assertEqual(results[1].filename, 'Fedora-20-x86_64-netinst.iso')
        self.assertEqual(
            results[1].directory.name,
            'pub/fedora/linux/releases/releases/20/Fedora/x86_64/iso')
        self.assertEqual(results[1].sha512, None)
        self.assertEqual(
            results[1].sha256,
            '376be7d4855ad6281cb139430606a782fd6189dcb01d7b61448e915802cc350f')

        self.assertEqual(
            results[2].filename, 'Fedora-Live-Desktop-x86_64-20-1.iso')
        self.assertEqual(
            results[2].directory.name,
            'pub/fedora/linux/releases/releases/20/Live/x86_64')
        self.assertEqual(results[2].sha512, None)
        self.assertEqual(
            results[2].sha256,
            'cc0333be93c7ff2fb3148cb29360d2453f78913cc8aa6c6289ae6823372a77d2')

        self.assertEqual(
            results[3].filename, 'Fedora-Live-KDE-x86_64-20-1.iso')
        self.assertEqual(
            results[3].directory.name,
            'pub/fedora/linux/releases/releases/20/Live/x86_64')
        self.assertEqual(results[3].sha512, None)
        self.assertEqual(
            results[3].sha256,
            '08360a253b4a40dff948e568dba1d2ae9d931797f57aa08576b8b9f1ef7e4745')

        self.assertEqual(results[4].filename, 'summary')
        self.assertEqual(
            results[4].directory.name,
            'pub/fedora/linux/releases/atomic/rawhide')
        self.assertEqual(
            results[4].sha256,
            '6b439b70ecb1941e0e2e0ea0817a66715067cbd96d4367f4cd23ca287aeb14cb')
        self.assertEqual(
            results[4].sha512,
            '6f3cafa7f16b796a6051f740de17344542feb8b2285e3ccd9b141217fbb5f0'
            'b602c2389e4a40fe3b1aeac6f853b4c6d2d6c863e3649f567bd1af2aea502f'
            'd9e8')

        self.assertEqual(results[5].filename, 'summary')
        self.assertEqual(
            results[5].directory.name,
            'pub/fedora/linux/releases/atomic/21')
        self.assertEqual(
            results[5].sha256,
            '6b439b70ecb1941e0e2e0ea0817a66715067cbd96d4367f4cd23ca287aeb14cb')
        self.assertEqual(
            results[5].sha512,
            '6f3cafa7f16b796a6051f740de17344542feb8b2285e3ccd9b141217fbb5f0'
            'b602c2389e4a40fe3b1aeac6f853b4c6d2d6c863e3649f567bd1af2aea502f'
            'd9e8')

        self.assertEqual(results[6].filename, 'repomd.xml')
        self.assertEqual(
            results[6].directory.name,
            'pub/fedora/linux/releases/releases/20/Fedora/source/SRPMS/repodata')
        self.assertEqual(
            results[6].sha256,
            '9a4738934092cf17e4540ee9cab741e922eb8306875ae5621feb01ebeb1f67f2')
        self.assertEqual(
            results[6].sha512,
            '3351c7a6b1d2bd94e375d09324a9280b8becfe4dea40a227c3b270ddcedb19'
            'f420eec3f2c6a39a1edcdf52f80d31eb47a0ba25057ced2e3182dd212bc746'
            '6ba2')

        self.assertEqual(results[7].filename, 'repomd.xml')
        self.assertEqual(
            results[7].directory.name,
            'pub/fedora/linux/releases/releases/20/Fedora/x86_64/os/repodata')
        self.assertEqual(
            results[7].sha256,
            '108b4102829c0839c7712832577fe7da24f0a9491f4dc25d4145efe6aced2ebf')
        self.assertEqual(
            results[7].sha512,
            '50ed8cb8f4daf8bcd1d0ccee1710b8a87ee8de5861fb15a1023d6558328795'
            'f42dade3e025c09c20ade36c77a3a82d9cdce1a2e2ad171f9974bc1889b591'
            '8020')

        results = mirrormanager2.lib.get_host_category_dirs(self.session)
        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(UMDLTest)
    unittest.TextTestRunner(verbosity=10).run(SUITE)
