import turbogears
from sqlobject import *
from mirrormanager.model import *
import hashlib

def initialize_filedetail():
    for fd in FileDetail.select():
        fd.sha256 = None
        fd.sha512 = None

def fill_filedetail():    
    for r in Repository.select():
        d = r.directory
        try:
            d = Directory.byName("%s/repodata" % (d.name))
        except:
            print "warning: Repository at Directory %s missing repodata subdir" % d.name
            continue
        for fd in d.fileDetails:
            if fd.filename == 'repomd.xml':
                try:
                    fname = "%s/repomd.xml" % (fd.directory.name)
                    f = open(fname, 'rb')
                    s = f.read()
                    f.close()
                    fd.sha256 = hashlib.sha256(s).hexdigest()
                    fd.sha512 = hashlib.sha512(s).hexdigest()
                    del s
                except:
                    print "warning: couldn't update sha checksums for %s" % d.name
                # only add to the most recent one
                break

def fill_arch():
    primary = ('i386', 'x86_64', 'ppc')
    for a in Arch.select():
        a.publiclist = (a.name != 'source')
        a.primary = (a.name in primary)

def update_schema():
    Arch.sqlmeta.addColumn(BoolCol('publiclist', default=True), updateSchema=True)
    Arch.sqlmeta.addColumn(BoolCol('primary', default=True), updateSchema=True)
    FileDetail.sqlmeta.addColumn(UnicodeCol('sha256', default=None), updateSchema=True)
    FileDetail.sqlmeta.addColumn(UnicodeCol('sha512', default=None), updateSchema=True)

def update():
    update_schema()
    fill_arch()
    initialize_filedetail()
    fill_filedetail()
