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
MirrorManager2 local login flask controller.
'''

import datetime

import flask
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from sqlalchemy.exc import SQLAlchemyError

import mirrormanager2.forms
import mirrormanager2.lib
from mirrormanager2 import APP, SESSION, is_mirrormanager_admin
from mirrormanager2.lib import model


@APP.route('/user/new', methods=['GET', 'POST'])
def new_user():
    """ Create a new user.
    """
    form = mirrormanager2.forms.NewUserForm()
    if form.validate_on_submit():

        username = form.user_name.data
        if mirrormanager2.lib.get_user_by_username(
                SESSION, username):
            flask.flash('Username already taken.', 'error')
            return flask.redirect(flask.request.url)

        email = form.email_address.data
        if mirrormanager2.lib.get_user_by_email(SESSION, email):
            flask.flash('Email address already taken.', 'error')
            return flask.redirect(flask.request.url)

        token = mirrormanager2.lib.id_generator(40)

        user = model.User()
        user.token = token
        form.populate_obj(obj=user)
        SESSION.add(user)

        try:
            SESSION.flush()
            flask.flash(
                'User created, please check your email to activate the '
                'account')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not create user.')
            APP.logger.debug('Could not create user.')
            APP.logger.exception(err)

        SESSION.commit()

        return flask.redirect(flask.url_for('auth_login'))

    return flask.render_template(
        'user_new.html',
        form=form,
    )


@APP.route('/dologin', methods=['POST'])
def do_login():
    """ Lo the user in user.
    """
    form = mirrormanager2.forms.LoginForm()
    next_url = flask.request.args.get('next_url')
    if not next_url or next_url == 'None':
        next_url = flask.url_for('index')

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user_obj = mirrormanager2.lib.get_user_by_username(SESSION, username)
        if not user_obj or user_obj.password != password:
            flask.flash('Username or password invalid.', 'error')
            return flask.redirect('login')
        elif user_obj.token:
            flask.flash(
                'Invalid user, did you confirm the creation with provided '
                'by email?', 'error')
            return flask.redirect('login')
        else:
            visit_key = mirrormanager2.lib.id_generator(40)
            expiry = datetime.datetime.now() + APP.config.get(
                'PERMANENT_SESSION_LIFETIME')
            session = model.UserVisit(
                user_id=user_obj.id,
                visit_key=visit_key,
                expiry=expiry,
            )
            SESSION.add(session)
            try:
                SESSION.commit()
                flask.g.fas_user = user_obj
                flask.g.fas_session_id = visit_key
                flask.flash('Welcome %s' % user_obj.username)
            except SQLAlchemyError, err:  # pragma: no cover
                flask.flash(
                    'Could not set the session in the db, '
                    'please report this error to an admin', 'error')
                APP.logger.exception(err)

        return flask.redirect(next_url)
    else:
        flask.flash('Insufficient information provided', 'error')
    return flask.redirect('login')


@APP.route('/confirm/<token>')
def confirm_user(token):
    """ Confirm a user account.
    """
    user_obj = mirrormanager2.lib.get_user_by_token(SESSION, token)
    if not user_obj:
        flask.flash('No user associated with this token.', 'error')
    else:
        user_obj.token = None
        SESSION.add(user_obj)

        try:
            SESSION.commit()
            flask.flash('Email confirmed, account activated')
        except SQLAlchemyError, err:  # pragma: no cover
            flask.flash(
                'Could not set the account as active in the db, '
                'please report this error to an admin', 'error')
            APP.logger.exception(err)

    return flask.redirect(flask.url_for('index'))

#
# Methods specific to local login.
#


def send_confirmation_email(user):
    """ Sends the confirmation email asking the user to confirm its email
    address.
    """

    message = """ Dear %(username)s,

Thank you for registering on MirrorManager at %(url)s.

To finish your registration, please click on the following link or copy/paste
it in your browser:
  %(url)/%(confirm_root)

You account will not be activated until you finish this step.

Sincerely,
Your MirrorManager admin.
""" % (
        {
            'username': user.username, 'url': flask.request.base_url,
            'confirm_root': flask.url_for('confirm_user', token=user.token)
        })

    mirrormanager2.notifications.email_publish(
        to_email=user.email_address,
        subject='[MirrorManager] Confirm your user account',
        message=message,
        from_email=APP.config.get('EMAIL_FROM', 'nobody@fedoraproject.org'),
        smtp_server=APP.config.get('SMTP_SERVER', 'localhost')
    )


def logout():
    """ Log the user out by expiring the user's session.
    """
    flask.g.fas_session_id = None
    flask.g.fas_user = None

    flask.flash('You have been logged out')


def _check_session_cookie():
    """ Set the user into flask.g if the user is logged in.
    """
    cookie_name = APP.config.get('MM_COOKIE_NAME', 'MirrorManager')
    session_id = None
    user = None

    if cookie_name and cookie_name in flask.request.cookies:
        sessionid = flask.request.cookies[cookie_name]
        session = mirrormanager2.lib.get_session_by_visitkey(
            SESSION, sessionid)
        if session and session.user:
            now = datetime.datetime.now()
            new_expiry = now + APP.config.get('PERMANENT_SESSION_LIFETIME')
            if now > session.expiry:
                flask.flash('Session timed-out', 'error')
            else:
                session_id = session.visit_key
                user = session.user

                session.expiry = new_expiry
                SESSION.add(session)
                try:
                    SESSION.commit()
                except SQLAlchemyError, err:  # pragma: no cover
                    flask.flash(
                        'Could not prolong the session in the db, '
                        'please report this error to an admin', 'error')
                    APP.logger.exception(err)

    flask.g.fas_session_id = session_id
    flask.g.fas_user = user


def _send_session_cookie(response):
    """ Set the session cookie if the user is authenticated. """
    cookie_name = APP.config.get('MM_COOKIE_NAME', 'MirrorManager')
    secure = APP.config.get('MM_COOKIE_REQUIRES_HTTPS', True)

    response.set_cookie(
        key=cookie_name,
        value=flask.g.fas_session_id or '',
        secure=secure,
        httponly=True,
    )
    return response
