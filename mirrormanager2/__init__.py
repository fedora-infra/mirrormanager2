# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
MirrorManager2 main flask controller.
'''


import logging
import logging.handlers
import os
import sys

import flask

from functools import wraps
from flask.ext.admin import Admin
from sqlalchemy.exc import SQLAlchemyError

__version__ = '2.0.1'

APP = flask.Flask(__name__)

APP.config.from_object('mirrormanager2.default_config')
if 'MM2_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('MM2_CONFIG')

ADMIN = Admin(APP)


if APP.config.get('MM_AUTHENTICATION') == 'fas':
    # Use FAS for authentication
    from flask.ext.fas_openid import FAS
    FAS = FAS(APP)


# Points the template and static folders to the desired theme
APP.template_folder = os.path.join(
    APP.template_folder, APP.config['THEME_FOLDER'])
APP.static_folder = os.path.join(
    APP.static_folder, APP.config['THEME_FOLDER'])


# Set up the logger
## Send emails for big exception
MAIL_HANDLER = logging.handlers.SMTPHandler(
    APP.config.get('SMTP_SERVER', '127.0.0.1'),
    'nobody@fedoraproject.org',
    APP.config.get('MAIL_ADMIN', 'admin@fedoraproject.org'),
    'MirrorManager2 error')
MAIL_HANDLER.setFormatter(logging.Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
'''))
MAIL_HANDLER.setLevel(logging.ERROR)
if not APP.debug:
    APP.logger.addHandler(MAIL_HANDLER)

# Log to stderr as well
STDERR_LOG = logging.StreamHandler(sys.stderr)
STDERR_LOG.setLevel(logging.INFO)
APP.logger.addHandler(STDERR_LOG)

LOG = APP.logger


import mirrormanager2.lib as mmlib
import mirrormanager2.forms as forms
import mirrormanager2.lib.model as model


SESSION = mmlib.create_session(APP.config['DB_URL'])


def is_mirrormanager_admin(user):
    """ Is the user a mirrormanager admin.
    """
    if not user:
        return False
    if APP.config.get('MM_AUTHENTICATION', None) == 'fas':
        if not user.cla_done or len(user.groups) < 1:
            return False

        admins = APP.config['ADMIN_GROUP']
        if isinstance(admins, basestring):
            admins = [admins]
        admins = set(admins)

        return len(admins.intersection(set(user.groups))) > 0
    else:
        return user in APP.config['ADMIN_GROUP']


## Flask application

@APP.context_processor
def inject_variables():
    """ Inject some variables into every template.
    """
    admin = False
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user:
        admin = is_mirrormanager_admin(flask.g.fas_user)

    return dict(
        is_admin=admin,
        version=__version__
    )

@APP.route('/')
def index():
    """ Displays the index page.
    """
    return flask.render_template(
        'index.html',
    )


@APP.route('/site/new', methods=['GET', 'POST'])
def site_new():
    """ Create a new site.
    """
    form = forms.AddSiteForm()
    if form.validate_on_submit():
        site = model.Site()
        SESSION.add(site)
        form.populate_obj(obj=site)
        site.created_by = flask.g.fas_user.username

        try:
            SESSION.flush()
            flask.flash('Site added')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not create the new site')
            APP.logger.debug('Could not create the new site')
            APP.logger.exception(err)
            return flask.redirect(flask.url_for('index'))

        try:
            msg = add_admin_to_site(SESSION, site, flask.g.fas_user.username)
            fask.flash(msg)
        except SQLAlchemyError as err:
            SESSION.rollback()
            APP.logger.debug(
                'Could not add admin "%s" to site "%s"' % (
                    flask.g.fas_user.username, site))
            APP.logger.exception(err)

        SESSION.commit()
        return flask.redirect(flask.url_for('index'))

    return flask.render_template(
        'site_new.html',
        form=form,
    )


@APP.route('/site/<site_id>')
def site_view(site_id):
    """ View information about a given site.
    """
    siteobj = mmlib.get_site(SESSION, site_id)

    if siteobj is None:
        flask.abort(404, 'Site not found')

    form = forms.AddSiteForm(obj=siteobj)
    if form.validate_on_submit():
        obj = form.populate_obj(obj=siteobj)
        SESSION.commit()
        flask.flash('Site Updated')
        return flask.redirect(flask.url_for('index'))

    return flask.render_template(
        'site.html',
        site=siteobj,
        form=form,
    )


@APP.route('/host/<site_id>/new', methods=['GET', 'POST'])
def host_new(site_id):
    """ Create a new host.
    """
    siteobj = mmlib.get_site(SESSION, site_id)

    if siteobj is None:
        flask.abort(404, 'Site not found')

    form = forms.AddHostForm()
    if form.validate_on_submit():
        host = model.Host()
        SESSION.add(host)
        host.site_id = siteobj.id
        form.populate_obj(obj=host)
        host.bandwidth_int = int(host.bandwidth_int)
        host.asn = None if not host.asn else int(host.asn)

        try:
            SESSION.flush()
            flask.flash('Host added')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not create the new host')
            APP.logger.debug('Could not create the new host')
            APP.logger.exception(err)

        SESSION.commit()
        return flask.redirect(flask.url_for('site_view', site_id=site_id))

    return flask.render_template(
        'host_new.html',
        form=form,
        site=siteobj,
    )


@APP.route('/host/<host_id>', methods=['GET', 'POST'])
def host_view(host_id):
    """ Create a new host.
    """
    hostobj = mmlib.get_host(SESSION, host_id)

    if hostobj is None:
        flask.abort(404, 'Host not found')

    form = forms.AddHostForm(obj=hostobj)
    if form.validate_on_submit():
        form.populate_obj(obj=host)
        host.bandwidth_int = int(host.bandwidth_int)
        host.asn = None if not host.asn else int(host.asn)

        try:
            SESSION.flush()
            flask.flash('Host updated')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not update the host')
            APP.logger.debug('Could not update the host')
            APP.logger.exception(err)

        SESSION.commit()
        return flask.redirect(flask.url_for('host_view', host_id=host_id))

    return flask.render_template(
        'host.html',
        form=form,
        host=hostobj,
    )


@APP.route('/host/<host_id>/host_acl_ip/new', methods=['GET', 'POST'])
def host_acl_ip_new(host_id):
    """ Create a new host_acl_ip.
    """
    hostobj = mmlib.get_host(SESSION, host_id)

    if hostobj is None:
        flask.abort(404, 'Host not found')

    form = forms.AddHostAclIpForm()
    if form.validate_on_submit():
        host_acl = model.HostAclIp()
        SESSION.add(host_acl)
        host_acl.host_id = hostobj.id
        form.populate_obj(obj=host_acl)

        try:
            SESSION.flush()
            flask.flash('Host ACL IP added')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not add ACL IP to the host')
            APP.logger.debug('Could not add ACL IP to the host')
            APP.logger.exception(err)

        SESSION.commit()
        return flask.redirect(flask.url_for('host_view', host_id=host_id))

    return flask.render_template(
        'host_acl_ip_new.html',
        form=form,
        host=hostobj,
    )


@APP.route('/host/<host_id>/host_acl_ip/<host_acl_ip_id>/delete',
           methods=['POST'])
def host_acl_ip_delete(host_id, host_acl_ip_id):
    """ Delete a host_acl_ip.
    """
    hostobj = mmlib.get_host(SESSION, host_id)

    if hostobj is None:
        flask.abort(404, 'Host not found')

    hostaclobj = mmlib.get_host_acl_ip(SESSION, host_acl_ip_id)

    if hostaclobj is None:
        flask.abort(404, 'Host ACL IP not found')
    else:
        SESSION.delete(hostaclobj)
    try:
        SESSION.flush()
        flask.flash('Host ACL IP deleted')
    except SQLAlchemyError as err:
        SESSION.rollback()
        flask.flash('Could not add ACL IP to the host')
        APP.logger.debug('Could not add ACL IP to the host')
        APP.logger.exception(err)

    SESSION.commit()
    return flask.redirect(flask.url_for('host_view', host_id=host_id))


@APP.route('/host/<host_id>/netblock/new', methods=['GET', 'POST'])
def host_netblock_new(host_id):
    """ Create a new host_netblock.
    """
    hostobj = mmlib.get_host(SESSION, host_id)

    if hostobj is None:
        flask.abort(404, 'Host not found')

    form = forms.AddHostNetblockForm()
    if form.validate_on_submit():
        host_netblock = model.HostNetblock()
        SESSION.add(host_netblock)
        host_netblock.host_id = hostobj.id
        form.populate_obj(obj=host_netblock)

        try:
            SESSION.flush()
            flask.flash('Host netblock added')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not add netblock to the host')
            APP.logger.debug('Could not add netblock to the host')
            APP.logger.exception(err)

        SESSION.commit()
        return flask.redirect(flask.url_for('host_view', host_id=host_id))

    return flask.render_template(
        'host_netblock_new.html',
        form=form,
        host=hostobj,
    )


@APP.route('/host/<host_id>/host_netblock/<host_netblock_id>/delete',
           methods=['POST'])
def host_netblock_delete(host_id, host_netblock_id):
    """ Delete a host_netblock.
    """
    hostobj = mmlib.get_host(SESSION, host_id)

    if hostobj is None:
        flask.abort(404, 'Host not found')

    hostnetbobj = mmlib.get_host_netblock(SESSION, host_netblock_id)

    if hostnetbobj is None:
        flask.abort(404, 'Host netblock not found')
    else:
        SESSION.delete(hostnetbobj)
    try:
        SESSION.commit()
        flask.flash('Host netblock deleted')
    except SQLAlchemyError as err:
        SESSION.rollback()
        flask.flash('Could not delete netblock of the host')
        APP.logger.debug('Could not delete netblock of the host')
        APP.logger.exception(err)

    return flask.redirect(flask.url_for('host_view', host_id=host_id))


@APP.route('/mirrors')
def list_mirrors():
    """ Displays the page listing all mirrors.
    """
    mirrors = mmlib.get_mirrors(
        SESSION,
        private=False,
        site_private=False,
        admin_active=True,
        user_active=True,
        site_admin_active=True,
        site_user_active=True,
        #last_checked_in=True,
        #last_crawled=True,
        up2date=True,
        host_category_url_private=False,
    )

    return flask.render_template(
        'mirrors.html',
        mirrors=mirrors,
    )


@APP.route('/login', methods=['GET', 'POST'])
def auth_login():  # pragma: no cover
    """ Login mechanism for this application.
    """
    next_url = flask.url_for('index')
    if 'next' in flask.request.values:
        next_url = flask.request.values['next']

    if next_url == flask.url_for('auth_login'):
        next_url = flask.url_for('index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return flask.redirect(next_url)
    else:
        return FAS.login(return_url=next_url)


@APP.route('/logout')
def auth_logout():
    """ Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    """
    next_url = flask.url_for('index')
    if 'next' in flask.request.values:  # pragma: no cover
        next_url = flask.request.values['next']

    if next_url == flask.url_for('auth_login'):  # pragma: no cover
        next_url = flask.url_for('index')
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
        flask.flash("You are no longer logged-in")
    return flask.redirect(next_url)

import admin
