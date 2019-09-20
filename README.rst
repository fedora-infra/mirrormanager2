Fedora MirrorManager
====================

MirrorManager2 is a rewrite of `mirrormanager <https://pagure.io/mirrormanager/>`_
using flask and SQLAlchemy.

MirrorManager is the application that keeps track of the nearly 400 public mirrors,
and over 300 private mirrors, that carry Fedora, EPEL, and RHEL content, and is used
by rpmfusion.org, a third party repository. It automatically selects the "best"
mirror for a given user based on a set of fallback heuristics.

:Github mirror: https://github.com/fedora-infra/mirrormanager2
:Mailing list for announcements and discussions: https://lists.fedoraproject.org/archives/list/mirror-admin@lists.fedoraproject.org/

Hacking
-------

Hacking with Vagrant
~~~~~~~~~~~~~~~~~~~~
Quickly start hacking on mirrormanager2 using the vagrant setup that is included
in the repo is super simple.

First, make a copy of the Vagrantfile example::

    $ cp Vagrantfile.example Vagrantfile

Next, install Ansible, Vagrant and the vagrant-libvirt plugin from the official Fedora
repos::

    $ sudo dnf install ansible vagrant vagrant-libvirt vagrant-sshfs


Now, from within main directory (the one with the Vagrantfile in it) of your git
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

First, set up a virtualenv::

    $ sudo yum install python-virtualenv
    $ virtualenv my-MirrorMan-env
    $ source my-MirrorMan-env/bin/activate

Issuing that last command should change your prompt to indicate that you are
operating in an active virtualenv.

Next, install your dependencies::

    (my-MirrorMan-env)$ pip install -r requirements.txt

Now the protobuf deinition needs to be compiled to Python::

    (my-MirrorMan-env)$ protoc --python_out=mirrorlist mirrormanager.proto
    (my-MirrorMan-env)$ protoc --python_out=mirrormanager2/lib mirrormanager.proto

You should then create your own sqlite database for your development instance of
mirrormanager2::

    (my-MirrorMan-env)$ python createdb.py

If all goes well, you can start a development instance of the server by
running::

    (my-MirrorMan-env)$ python runserver.py

Open your browser and visit http://localhost:5000 to check it out.

Once you made your changes please run the test suite to verify that nothing
covered by tests has been broken::

    (my-MirrorMan-env)$ ./runtests.sh
