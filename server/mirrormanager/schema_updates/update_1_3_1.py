import turbogears
from sqlobject import *
from mirrormanager.model import *

def update_host():
    rc = False
    try:
        Host.asn = Host.sqlmeta.addColumn(IntCol(name='asn', default=None), changeSchema=True)
        Host.asn_clients = Host.sqlmeta.addColumn(BoolCol(name='asn_clients', default=True), changeSchema=True)
        rc = True
    except:
        pass
    return rc

def initialize_host():
    for h in Host.select():
        h.asn = None
        h.asn_clients = True
        h.sync()


def update():
    rc = update_host()
    if rc:
        initialize_host()
