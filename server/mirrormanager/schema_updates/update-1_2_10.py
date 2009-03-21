import turbogears
from sqlobject import *
from mirrormanager.model import *

def update():
    Arch.sqlmeta.addColumn(BoolCol('publiclist', default=True), updateSchema=True)
    Arch.sqlmeta.addColumn(BoolCol('primary', default=True), updateSchema=True)
    for a in Arch.select():
        a.publiclist = True
        a.primary = True
        a.sync()

    FileDetail.sqlmeta.addColumn(UnicodeCol('sha256', default=None), updateSchema=True)
    FileDetail.sqlmeta.addColumn(UnicodeCol('sha512', default=None), updateSchema=True)
    for f in FileDetail.select():
        f.sha256 = None
        f.sha512 = None
        f.sync()
