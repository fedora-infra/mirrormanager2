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
                    fname = "/%s/repomd.xml" % (d.name)
                    f = open(fname, 'rb')
                    s = f.read()
                    f.close()
                    h  = hashlib.sha256(s).hexdigest()
                    print "sha256=%s" % h
                    fd.sha256 =h
                    fd.sha512 = hashlib.sha512(s).hexdigest()
                    del s
                except:
                    print "warning: couldn't update sha checksums for %s" % fname
                # only add to the most recent one
                break

def fill_arch():
    primary = ('i386', 'x86_64', 'ppc')
    for a in Arch.select():
        a.publiclist = (a.name != 'source')
        a.primaryArch = (a.name in primary)

def update_schema_arch():
    rc = False
    try:
        Arch.sqlmeta.delColumn('publiclist', changeSchema=False)
        c = Arch.sqlmeta.addColumn(BoolCol(name='publiclist', default=True), changeSchema=True)
        Arch.publiclist = c
        Arch.sqlmeta.delColumn('primaryArch', changeSchema=False)
        c = Arch.sqlmeta.addColumn(BoolCol(name='primaryArch', default=False), changeSchema=True)
        Arch.primaryArch = c
        rc = True
    except:
        pass
    return rc

def update_schema_filedetail():
    rc = False
    try:
        FileDetail.sqlmeta.delColumn('sha256', changeSchema=False)
        c = FileDetail.sqlmeta.addColumn(UnicodeCol(name='sha256', default=None), changeSchema=True)
        FileDetail.sha256 = c
        FileDetail.sqlmeta.delColumn('sha512', changeSchema=False)
        c = FileDetail.sqlmeta.addColumn(UnicodeCol(name='sha512', default=None), changeSchema=True)
        FileDetail.sha512 = c
        rc = True
    except:
        pass
    return rc

def update():
    rc = update_schema_arch()
    if rc:
        fill_arch()
    rc = update_schema_filedetail()
    if rc:
        initialize_filedetail()
        fill_filedetail()
