# -*- coding: utf-8 -*-

'''
mirrormanager2 tests.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

from contextlib import contextmanager
from flask import appcontext_pushed, g

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from mirrormanager2.app import APP, FAS, LOG
from mirrormanager2.lib import model

#DB_PATH = 'sqlite:///:memory:'
## A file database is required to check the integrity, don't ask
DB_PATH = 'sqlite:////tmp/test.sqlite'
FAITOUT_URL = 'http://209.132.184.152/faitout/'

if os.environ.get('BUILD_ID'):
    try:
        import requests
        req = requests.get('%s/new' % FAITOUT_URL)
        if req.status_code == 200:
            DB_PATH = req.text
            print 'Using faitout at: %s' % DB_PATH
    except:
        pass

LOG.handlers = []


@contextmanager
def user_set(APP, user):
    """ Set the provided user as fas_user in the provided application."""

    # Hack used to remove the before_request function set by
    # flask.ext.fas_openid.FAS which otherwise kills our effort to set a
    # flask.g.fas_user.
    APP.before_request_funcs[None] = []

    def handler(sender, **kwargs):
        g.fas_user = user

    with appcontext_pushed.connected_to(handler, APP):
        yield


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        if '///' in DB_PATH:
            dbfile = DB_PATH.split('///')[1]
            if os.path.exists(dbfile):
                os.unlink(dbfile)
        self.session = model.create_tables(DB_PATH, debug=False)
        APP.before_request(FAS._check_session)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        if '///' in DB_PATH:
            dbfile = DB_PATH.split('///')[1]
            if os.path.exists(dbfile):
                os.unlink(dbfile)

        self.session.rollback()
        self.session.close()

        #if DB_PATH.startswith('postgres'):
            #if 'localhost' in DB_PATH:
                #model.drop_tables(DB_PATH, self.session.bind)
            #else:
                #db_name = DB_PATH.rsplit('/', 1)[1]
                #req = requests.get(
                    #'%s/clean/%s' % (FAITOUT_URL, db_name))
                #print req.text


def create_base_items(session):
    ''' Insert some base information in the database.
    '''
    # Insert some Arch
    item = model.Arch(
        name='source',
        publiclist=False,
        primary_arch=False,
    )
    session.add(item)
    item = model.Arch(
        name='i386',
        publiclist=True,
        primary_arch=True,
    )
    session.add(item)
    item = model.Arch(
        name='x86_64',
        publiclist=True,
        primary_arch=True,
    )
    session.add(item)
    item = model.Arch(
        name='ppc',
        publiclist=True,
        primary_arch=False,
    )
    session.add(item)

    # Insert some Country
    item = model.Country(
        code='FR',
    )
    session.add(item)
    item = model.Country(
        code='US',
    )
    session.add(item)

    # Insert some Product
    item = model.Product(
        name='EPEL',
        publiclist=True,
    )
    session.add(item)
    item = model.Product(
        name='Fedora',
        publiclist=True,
    )
    session.add(item)

    session.commit()


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
