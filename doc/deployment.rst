Deployment
==========

From sources
------------

Clone the source::

 git clone https://github.com/fedora-infra/mirrormanager2.git

Install Poetry and run ``poetry install`` to install the dependencies.

Copy the configuration files::

  cp utility/mirrormanager2.cfg.sample mirrormanager2.cfg

Adjust the configuration files (secret key, database URL, admin group...).


Create the database scheme::

   MM2_CONFIG=/path/to/mirrormanager2.cfg python createdb.py

Set up the WSGI as described below.


From system-wide packages
-------------------------

Start by install mirrormanager2::

  dnf install mirrormanager2

Adjust the configuration files: ``/etc/mirrormanager2/mirrormanager2.cfg``.

Find the file used to create the database::

  rpm -ql mirrormanager22 |grep createdb.py

Create the database scheme::

   MM2_CONFIG=/etc/mirrormanager2/mirrormanager2.cfg python path/to/createdb.py

Set up the WSGI as described below.


Set-up WSGI
-----------

Start by installing ``mod_wsgi``::

  dnf install mod_wsgi


Then configure apache::

 sudo vim /etc/httd/conf.d/mirrormanager2.conf

uncomment the content of the file and adjust as desired.


Then edit the file ``/usr/share/mirrormanager2/mirrormanager2.wsgi`` and
adjust as needed.


Then restart apache and you should be able to access the website on
http://localhost/mirrormanager


.. note:: `Flask <http://flask.pocoo.org/>`_ provides also  some documentation
          on how to `deploy Flask application with WSGI and apache
          <http://flask.pocoo.org/docs/deploying/mod_wsgi/>`_.


For testing
-----------

See :doc:`development` if you want to run mirrormanager2 just to test it.

