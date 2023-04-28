# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.
# Copyright 2006 Duke University
# Copyright 2007-2016 Red Hat, Inc.
# Copyright 2017 Neal Gompa

"""
Assorted utility functions for pyrpmmd.
"""
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import os.path
import errno

import six

from rpmmd.Errors import MiscError

# Ugly hack to preserve Py2/Py3 compatibility
if six.PY3:
    unicode = str

_available_compression = ['gz', 'bz2']
try:
    import lzma
    _available_compression.append('xz')
except ImportError:
    lzma = None

import hashlib
_available_checksums = set(['md5', 'sha1', 'sha256', 'sha384', 'sha512'])

# some checksum types might be disabled
for ctype in list(_available_checksums):
    try:
        hashlib.new(ctype)
    except:
        print('Checksum type %s disabled' % repr(ctype), file=sys.stderr)
        _available_checksums.remove(ctype)
for ctype in 'sha256', 'sha1':
    if ctype in _available_checksums:
        _default_checksums = [ctype]
        break
else:
    raise ImportError('broken hashlib')

class Checksums:
    """ Generate checksum(s), on given pieces of data. Producing the
        Length and the result(s) when complete. """

    def __init__(self, checksums=None, ignore_missing=False, ignore_none=False):
        if checksums is None:
            checksums = _default_checksums
        self._sumalgos = []
        self._sumtypes = []
        self._len = 0

        done = set()
        for sumtype in checksums:
            if sumtype == 'sha':
                sumtype = 'sha1'
            if sumtype in done:
                continue

            if sumtype in _available_checksums:
                sumalgo = hashlib.new(sumtype)
            elif ignore_missing:
                continue
            else:
                raise MiscError('Error Checksumming, bad checksum type %s' % sumtype)
            done.add(sumtype)
            self._sumtypes.append(sumtype)
            self._sumalgos.append(sumalgo)
        if not done and not ignore_none:
            raise MiscError('Error Checksumming, no valid checksum type')

    def __len__(self):
        return self._len

    # Note that len(x) is assert limited to INT_MAX, which is 2GB on i686.
    length = property(fget=lambda self: self._len)

    def update(self, data):
        self._len += len(data)
        for sumalgo in self._sumalgos:
            sumalgo.update(data.encode('utf-8'))

    def read(self, fo, size=2**16):
        data = fo.read(size)
        self.update(data)
        return data

    def hexdigests(self):
        ret = {}
        for sumtype, sumdata in zip(self._sumtypes, self._sumalgos):
            ret[sumtype] = sumdata.hexdigest()
        return ret

    def hexdigest(self, checksum=None):
        if checksum is None:
            if not self._sumtypes:
                return None
            checksum = self._sumtypes[0]
        if checksum == 'sha':
            checksum = 'sha1'
        return self.hexdigests()[checksum]

    def digests(self):
        ret = {}
        for sumtype, sumdata in zip(self._sumtypes, self._sumalgos):
            ret[sumtype] = sumdata.digest()
        return ret

    def digest(self, checksum=None):
        if checksum is None:
            if not self._sumtypes:
                return None
            checksum = self._sumtypes[0]
        if checksum == 'sha':
            checksum = 'sha1'
        return self.digests()[checksum]


class AutoFileChecksums:
    """ Generate checksum(s), on given file/fileobject. Pretending to be a file
        object (overrrides read). """

    def __init__(self, fo, checksums, ignore_missing=False, ignore_none=False):
        self._fo       = fo
        self.checksums = Checksums(checksums, ignore_missing, ignore_none)

    def __getattr__(self, attr):
        return getattr(self._fo, attr)

    def read(self, size=-1):
        return self.checksums.read(self._fo, size)


def checksum(sumtype, file, CHUNK=2**16, datasize=None):
    """takes filename, hand back Checksum of it
       sumtype = md5 or sha/sha1/sha256/sha512 (note sha == sha1)
       filename = /path/to/file
       CHUNK=65536 by default"""
     
    # chunking brazenly lifted from Ryan Tomayko
    try:
        if not isinstance(file, six.string_types):
            fo = file # assume it's a file-like-object
        else:           
            fo = open(file, 'r')

        data = Checksums([sumtype])
        while data.read(fo, CHUNK):
            if datasize is not None and data.length > datasize:
                break

        if isinstance(file, six.binary_types):
            fo.close()
            
        # This screws up the length, but that shouldn't matter. We only care
        # if this checksum == what we expect.
        if datasize is not None and datasize != data.length:
            return '!%u!%s' % (datasize, data.hexdigest(sumtype))

        return data.hexdigest(sumtype)
    except (IOError, OSError) as e:
        raise MiscError('Error opening file for checksum: %s' % file)

_deletechars = ''.join(chr(i) for i in range(32) if i not in (9, 10, 13))

def to_xml(item, attrib=False):
    """ Returns xml-friendly utf-8 encoded string.
        Accepts utf-8, iso-8859-1, or unicode.
    """
    if isinstance(item, bytes):
        # check if valid utf8
        try: unicode(item, encoding='utf-8')
        except UnicodeDecodeError:
            # assume iso-8859-1
            item = unicode(item, encoding='iso-8859-1').encode('utf-8')
    elif isinstance(item, unicode):
        item = item.encode('utf-8')
    elif item is None:
        return ''
    else:
        raise ValueError('String expected, got %s' % repr(item))

    # compat cruft...
    item = item.rstrip()

    # kill invalid low bytes
    if six.PY2:
        item = item.translate(None, _deletechars)
    else:
        item = item.decode('utf-8').translate(_deletechars)

    # quote reserved XML characters
    item = item.replace('&', '&amp;')
    item = item.replace('<', '&lt;')
    item = item.replace('>', '&gt;')
    if attrib:
        item = item.replace('"', '&quot;')
        item = item.replace("'", '&apos;')

    return item

def stat_f(filename, ignore_EACCES=False):
    """ Call os.stat(), but don't die if the file isn't there. Returns None. """
    try:
        return os.stat(filename)
    except OSError as e:
        if e.errno in (errno.ENOENT, errno.ENOTDIR):
            return None
        if ignore_EACCES and e.errno == errno.EACCES:
            return None
        raise
