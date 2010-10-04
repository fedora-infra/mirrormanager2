from mirrormanager.model import Zone

def update():
    zone = Zone.createTable(ifNotExists=True)
