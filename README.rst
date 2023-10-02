Fedora MirrorManager
====================

MirrorManager2 is a rewrite of `mirrormanager <https://pagure.io/mirrormanager/>`_
using flask and SQLAlchemy.

MirrorManager is the application that keeps track of the nearly 400 public mirrors,
and over 300 private mirrors, that carry Fedora, EPEL, and RHEL content, and is used
by rpmfusion.org, a third party repository. It automatically selects the "best"
mirror for a given user based on a set of fallback heuristics.

The complete MirrorManager functionality requires `generate-mirrorlist-cache`
and `mirrorlist-server` which can be found at
https://github.com/adrianreber/mirrorlist-server.

Mailing list for announcements and discussions:
https://lists.fedoraproject.org/archives/list/mirror-admin@lists.fedoraproject.org/

Hacking
-------

Using Tinystage
~~~~~~~~~~~~~~~
MirrorManager2 authenticates using OpenID Connect. For this, it requires an
OIDC provider, and the tiny-stage environment provides that.

Download tiny-stage from Github with::

    $ git clone https://github.com/fedora-infra/tiny-stage
    $ cd tiny-stage

Now install Ansible, Vagrant and the vagrant-libvirt plugin from the official
Fedora repos, and startup tiny-stage::

    $ sudo dnf install ansible vagrant vagrant-libvirt vagrant-sshfs
    $ vagrant up ipa auth

It takes a bit of time, but tiny-stage will now be installed, with dummy users
and groups.


Hacking with Vagrant
~~~~~~~~~~~~~~~~~~~~
Quickly start hacking on mirrormanager2 using the vagrant setup that is included
in the repo is super simple.

From within main directory (the one with the Vagrantfile in it) of your git
checkout of mirrormanager2, run the ``vagrant up`` command to provision your dev
environment::

    $ vagrant up

When this command is completed (it may take a while) you will be able to the
command to start the mirrormanager server::

    $ vagrant ssh -c "pushd /vagrant/; python runserver.py --host '0.0.0.0'"

Once that is running, simply go to http://localhost:5000/ in your browser on
your host to see your running mirrormanager test instance.


Manual Setup
~~~~~~~~~~~~
Here are some preliminary instructions about how to stand up your own instance
of mirrormanager2. All required packages for MirrorManager2 are part of Fedora
or RHEL/CentOS/EPEL. In the following example we will, however use a virtualenv
and a sqlite database and we will install our dependencies from the Python
Package Index (PyPI).

Note: this setup still needs tiny-stage running.

First, install development dependencies::

    $ sudo dnf install poetry tox

Next, install MirrorManager's dependencies::

    $ poetry install

You also need to install and run ``oidc-register`` to register mirrormanager2
with tiny-stage. Tinystage has a self-signed certificate, it needs to be added
to the known certificates::

    $ poetry run pip install oidc-register
    $ curl -k https://ipsilon.tinystage.test/ca.crt >> $(poetry run python -m certifi)
    $ poetry run oidc-register https://ipsilon.tinystage.test/idp/openidc/ https://mirrormanager2.tinystage.test/authorize

You should then create your own sqlite database for your development instance of
mirrormanager2::

    $ poetry run ./createdb.py

If all goes well, you can start a development instance of the server by
running::

    $ poetry run ./runserver.py

Open your browser and visit http://localhost:5000 to check it out.

Once you made your changes please run the test suite to verify that nothing
covered by tests has been broken::

    $ tox
