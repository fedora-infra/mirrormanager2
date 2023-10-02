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


Run MirrorManager for development
---------------------------------

The instructions to setup MirrorManager are in the `README.rst`_ file.

.. _README.rst: https://github.com/fedora-infra/mirrormanager2/blob/master/README.rst


Coding standards
----------------

We are trying to make the code `PEP8-compliant
<http://www.python.org/dev/peps/pep-0008/>`_.  There is a `black tool
<http://pypi.python.org/pypi/black>`_ that can automatically format
your source.


We are also inspecting the code using `ruff
<http://pypi.python.org/pypi/ruff>`_ and want all tests to pass.

.. note:: both black and ruff are available in Fedora via yum:

          ::

            dnf install black ruff


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
