mirrormanager

This is a TurboGears (http://www.turbogears.org) project. It can be
started by running the start-mirrormanager.py script.

You'll need TurboGears, python-IPy and python-GeoIP installed at a
minimum.

To setup mirrormanager for the first time you have to run:

$ tg-admin -c dev.cfg sql create
 # dev.cfg is a simple config file for a development instance with
 # local account setup

$ tg-admin -c dev.cfg shell
>>> import mirrormanager.initial
 to exit
 # mirrormanager.initial uses the file mirromanager/initial.py
 # for the inital data in the test sqlite database
 # if you want that a few test users are created you have to remove
 # the comment at the before "add_test_groups_and_users()"
 # this creates a user test (password: test)
 # and admin (password: admin)

$ ./start-mirrormanager.py dev.cfg

Now you can use your browser to connect to http://localhost:8080/ and login.
