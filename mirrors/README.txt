mirrormanager

This is a TurboGears (http://www.turbogears.org) project. It can be
started by running the start-mirrormanager script.

You'll need TurboGears, python-IPy and python-GeoIP installed at a
minimum.

You must:

$ tg-admin -c dev.cfg sql create
$ tg-admin -c dev.cfg shell
>>> import mirrorsmanager.initial
 to exit

$ ./start-mirrormanager dev.cfg


