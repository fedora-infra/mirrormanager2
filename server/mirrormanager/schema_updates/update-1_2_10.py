import turbogears
from sqlobject import *
from mirrormanager.model import *

def update():
    Arch.sqlmeta.addColumn(BoolCol('publiclist', default=True), updateSchema=True)
    Arch.sqlmeta.addColumn(BoolCol('primary', default=True), updateSchema=True)
    primary = ('i386', 'x86_64', 'ppc')
    for a in Arch.select():
        a.publiclist = (a.name != 'source')
        a.primary = (a.name in primary)
        a.sync()
    Arch.sqlmeta.delColumn('idx')
    Arch.sqlmeta.addColumn(DatabaseIndex('fromRepo', 'toRepo', 'fromArch', 'toArch', dbName='idx', unique=True)

    FileDetail.sqlmeta.addColumn(UnicodeCol('sha256', default=None), updateSchema=True)
    FileDetail.sqlmeta.addColumn(UnicodeCol('sha512', default=None), updateSchema=True)
    for f in FileDetail.select():
        f.sha256 = None
        f.sha512 = None
        f.sync()
