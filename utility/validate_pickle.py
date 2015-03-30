#!/usr/bin/python

import cPickle
import sys
import unittest

if len(sys.argv) != 2:
    print 'Usage: validate_pickle.py <pickle_file>'
    sys.exit(1)

pickle_file = sys.argv[1]

data = {}

with open(pickle_file) as stream:
    data = cPickle.load(stream)

if data:
    print 'Pickle loaded with length {0}'.format(len(data))
