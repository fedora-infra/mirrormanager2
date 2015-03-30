#!/usr/bin/python
#
# This file is part of MirrorManager 2.
#
# validate_pickle.py by David Gay <dgay@redhat.com>
# Runs a series of checks on a MM2 pickle file to confirm its validity.
#
# Released under the MIT/X11 license.

import cPickle
import sys
import unittest

if len(sys.argv) != 2:
    print 'Usage: validate_pickle.py <pickle_file>'
    sys.exit(1)

pickle_file = sys.argv[1]

data = {}

print "Validating pickle {0}".format(pickle_file)

with open(pickle_file) as stream:
    data = cPickle.load(stream)

if data:
    print 'Pickle loaded. (length {0})'.format(len(data))
else:
    raise Exception('Failed to load pickle')

if len(data) < 1:
    raise Exception('Empty pickle')
