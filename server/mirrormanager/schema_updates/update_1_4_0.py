from mirrormanager.model import Zone, Schema

def update():
    Zone.createTable(ifNotExists=True)
    Schema.createTable(ifNotExists=True)
    if Schema.select().count() == 0:
        Schema(version=u'1.4')
