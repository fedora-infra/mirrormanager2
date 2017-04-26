Development
===========

Get the sources
---------------

Anonymous:

::

  git clone https://github.com/fedora-infra/mirrormanager2.git

Contributors:

::

  git clone git@github.com:fedora-infra/mirrormanager2.git


Dependencies
------------

The dependencies of mirrormanager2 are listed in the file ``requirements.txt``
at the top level of the sources.


.. note:: if you work in a `virtualenv <http://www.virtualenv.org/en/latest/>`_
          the installation of python-fedora might fail the first time you
          try, just try to run the command twice, the second time it should
          work.


Run MirrorManager for development
---------------------------------
Copy the configuration file::

 cp utility/mirrormanager2.cfg.sample mirrormanager2.cfg

Adjust the configuration file (secret key, database URL, admin group...)
See :doc:`configuration` for more detailed information about the
configuration.


Create the database scheme::

  ./createdb

Run the server::

  ./runserver

You should be able to access the server at http://localhost:5000


Every time you save a file, the project will be automatically restarted
so you can see your change immediatly.


Coding standards
----------------

We are trying to make the code `PEP8-compliant
<http://www.python.org/dev/peps/pep-0008/>`_.  There is a `pep8 tool
<http://pypi.python.org/pypi/pep8>`_ that can automatically check
your source.


We are also inspecting the code using `pylint
<http://pypi.python.org/pypi/pylint>`_ and aim of course for a 10/10 code
(but it is an assymptotic goal).

.. note:: both pep8 and pylint are available in Fedora via yum:

          ::

            yum install python-pep8 pylint


Send patch
----------

The easiest way to work on mirrormanager2 is to make your own branch in git,
make your changes to this branch, commit whenever you want, rebase on master,
whenever you need and when you are done, send the patch either by email,
via the trac or a pull-request (using git or github).


The workflow would therefore be something like:

::

   git branch <my_shiny_feature>
   git checkout <my_shiny_feature>
   <work>
   git commit file1 file2
   <more work>
   git commit file3 file4
   git checkout master
   git pull
   git checkout <my_shiny_feature>
   git rebase master
   git format-patch -2

This will create two patch files that you can send by email to submit in the
trac.

.. note:: You can send your patch by email to the `mirror-list-discuss mailing-list
          <http://www.redhat.com/mailman/listinfo/mirror-list-d>`_



Troubleshooting
---------------

+ Login fails in development mode

  The Flask FAS extension requires a secure cookie which ensures that it is
  always encrypted during client/server exchanges.
  This makes the authentication cookie less likely to be exposed to cookie
  theft by eavesdropping.

  You can disable the secure cookie for testing purposes by setting the
  configuration key ``FAS_HTTPS_REQUIRED`` to False.

  .. WARNING::
     Do not use this option in production as it causes major security issues

