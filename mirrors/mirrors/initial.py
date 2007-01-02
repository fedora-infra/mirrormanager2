from mirrors.model import Config, Protocol

#check if a configuration already exists. Create one if it doesn't
if not Config.select().count():
    print "Creating Config"
    Config()

if not Protocol.select().count():
    print "Creating Protocols"
    Protocol(name="http")
    Protocol(name="ftp")
    Protocol(name="rsync")

