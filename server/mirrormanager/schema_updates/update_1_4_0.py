from mirrormanager.model import Location, Schema

def update():
    Location.createTable(ifNotExists=True)
    Schema.createTable(ifNotExists=True)
    if Schema.select().count() == 0:
        Schema(version=u'1.4')
