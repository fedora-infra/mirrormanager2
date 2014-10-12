Fedora MirrorManager
====================

MirrorManager2 is a rewrite of `mirrormanager <https://fedorahosted.org/mirrormanager/>`_
using flask and SQLAlchemy.

MirrorManager is the application that keeps track of the nearly 400 public mirrors,
and over 300 private mirrors,that carry Fedora, EPEL, and RHEL content, and is used
by rpmfusion.org, a third party repository. It automatically selects the "best"
mirror for a given user based on a set of fallback heuristics.
For more details `mirrormanager <https://fedorahosted.org/mirrormanager/>`_

:Github mirror: https://github.com/fedora-infra/mirrormanager2
:Mailing list: https://lists.fedorahosted.org/mailman/listinfo/packagedb

Hacking
-------

Here are some preliminary instructions about how to stand up your own instance
of mirrormanager2.  We'll use a virtualenv and a mariadb database and we'll install
our dependencies from the Python Package Index (PyPI).

First, set up a virtualenv::

    $ sudo yum install python-virtualenv
    $ virtualenv my-MirrorMan-env
    $ source my-MirrorMan-env/bin/activate

Issueing that last command should change your prompt to indicate that you are
operating in an active virtualenv.

Next, install your dependencies::

    (my-MirrorMan-env)$ pip install -r requirements.txt

You should then create your own mariadb database for your development instance of
mirrormanager2::

    (my-MirrorMan-env)$ python createdb.py

If all goes well, you can start a development instance of the server by
running::

    (my-MirrorMan-env)$ python runserver.py

Open your browser and visit http://localhost:5000 to check it out.






