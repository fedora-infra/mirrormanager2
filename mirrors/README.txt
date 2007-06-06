mirrors

This is a TurboGears (http://www.turbogears.org) project. It can be
started by running the start-mirrors.py script.

You'll need TurboGears, python-IPy and python-GeoIP installed at a
minimum.

You must:

$ tg-admin -c dev.cfg sql create
$ tg-admin -c dev.cfg shell
>>> import mirrors.initial
 to exit

$ ./start-mirrors dev.cfg


