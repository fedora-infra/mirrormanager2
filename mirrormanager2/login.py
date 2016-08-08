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

import hashlib
import datetime

import flask
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.exc import SQLAlchemyError

import mirrormanager2.login_forms as forms
import mirrormanager2.lib
import mirrormanager2.lib.notifications
from mirrormanager2.app import APP, SESSION, is_mirrormanager_admin
from mirrormanager2.lib import model


@APP.route('/user/new', methods=['GET', 'POST'])
def new_user():
    """ Create a new user.
    """
    form = forms.NewUserForm()
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

        password = '%s%s' % (
            form.password.data, APP.config.get('PASSWORD_SEED', None))
        form.password.data = hashlib.sha512(password).hexdigest()

        token = mirrormanager2.lib.id_generator(40)

        user = model.User()
        user.token = token
        form.populate_obj(obj=user)
        SESSION.add(user)

        try:
            SESSION.flush()
            send_confirmation_email(user)
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
    form = forms.LoginForm()
    next_url = flask.request.args.get('next_url')
    if not next_url or next_url == 'None':
        next_url = flask.url_for('index')

    if form.validate_on_submit():
        username = form.username.data
        password = '%s%s' % (
            form.password.data, APP.config.get('PASSWORD_SEED', None))
        password = hashlib.sha512(password).hexdigest()

        user_obj = mirrormanager2.lib.get_user_by_username(SESSION, username)
        if not user_obj or user_obj.password != password:
            flask.flash('Username or password invalid.', 'error')
            return flask.redirect(flask.url_for('auth_login'))
        elif user_obj.token:
            flask.flash(
                'Invalid user, did you confirm the creation with the url '
                'provided by email?', 'error')
            return flask.redirect(flask.url_for('auth_login'))
        else:
            visit_key = mirrormanager2.lib.id_generator(40)
            expiry = datetime.datetime.now() + APP.config.get(
                'PERMANENT_SESSION_LIFETIME')
            session = model.UserVisit(
                user_id=user_obj.id,
                user_ip=flask.request.remote_addr,
                visit_key=visit_key,
                expiry=expiry,
            )
            SESSION.add(session)
            try:
                SESSION.commit()
                flask.g.fas_user = user_obj
                flask.g.fas_session_id = visit_key
                flask.flash('Welcome %s' % user_obj.username)
            except SQLAlchemyError as err:  # pragma: no cover
                flask.flash(
                    'Could not set the session in the db, '
                    'please report this error to an admin', 'error')
                APP.logger.exception(err)

        return flask.redirect(next_url)
    else:
        flask.flash('Insufficient information provided', 'error')
    return flask.redirect(flask.url_for('auth_login'))


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
            return flask.redirect(flask.url_for('auth_login'))
        except SQLAlchemyError as err:  # pragma: no cover
            flask.flash(
                'Could not set the account as active in the db, '
                'please report this error to an admin', 'error')
            APP.logger.exception(err)

    return flask.redirect(flask.url_for('index'))


@APP.route('/password/lost', methods=['GET', 'POST'])
def lost_password():
    """ Method to allow a user to change his/her password assuming the email
    is not compromised.
    """
    form = forms.LostPasswordForm()
    if form.validate_on_submit():

        username = form.username.data
        user_obj = mirrormanager2.lib.get_user_by_username(SESSION, username)
        if not user_obj:
            flask.flash('Username invalid.', 'error')
            return flask.redirect(flask.url_for('auth_login'))
        elif user_obj.token:
            flask.flash(
                'Invalid user, did you confirm the creation with the url '
                'provided by email? Or did you already ask for a password '
                'change?', 'error')
            return flask.redirect(flask.url_for('auth_login'))

        token = mirrormanager2.lib.id_generator(40)
        user_obj.token = token
        SESSION.add(user_obj)

        try:
            SESSION.commit()
            send_lostpassword_email(user_obj)
            flask.flash(
                'Check your email to finish changing your password')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash(
                'Could not set the token allowing changing a password.',
                'error')
            APP.logger.debug('Password lost change - Error setting token.')
            APP.logger.exception(err)

        return flask.redirect(flask.url_for('auth_login'))

    return flask.render_template(
        'password_change.html',
        form=form,
    )


@APP.route('/password/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """ Method to allow a user to reset his/her password.
    """
    form = forms.ResetPasswordForm()

    user_obj = mirrormanager2.lib.get_user_by_token(SESSION, token)
    if not user_obj:
        flask.flash('No user associated with this token.', 'error')
        return flask.redirect(flask.url_for('auth_login'))
    elif not user_obj.token:
        flask.flash(
            'Invalid user, this user never asked for a password change',
            'error')
        return flask.redirect(flask.url_for('auth_login'))

    if form.validate_on_submit():

        password = '%s%s' % (
            form.password.data, APP.config.get('PASSWORD_SEED', None))
        user_obj.password = hashlib.sha512(password).hexdigest()
        user_obj.token = None
        SESSION.add(user_obj)

        try:
            SESSION.commit()
            flask.flash(
                'Password changed')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not set the new password.', 'error')
            APP.logger.debug(
                'Password lost change - Error setting password.')
            APP.logger.exception(err)

        return flask.redirect(flask.url_for('auth_login'))

    return flask.render_template(
        'password_reset.html',
        form=form,
        token=token,
    )

#
# Methods specific to local login.
#


def send_confirmation_email(user):
    """ Sends the confirmation email asking the user to confirm its email
    address.
    """

    url = APP.config.get('APPLICATION_URL', flask.request.url_root)

    message = """ Dear %(username)s,

Thank you for registering on MirrorManager at %(url)s.

To finish your registration, please click on the following link or copy/paste
it in your browser:
  %(url)s/%(confirm_root)s

You account will not be activated until you finish this step.

Sincerely,
Your MirrorManager admin.
""" % (
        {
            'username': user.username, 'url': url or flask.request.url_root,
            'confirm_root': flask.url_for('confirm_user', token=user.token)
        })

    mirrormanager2.lib.notifications.email_publish(
        to_email=user.email_address,
        subject='[MirrorManager] Confirm your user account',
        message=message,
        from_email=APP.config.get('EMAIL_FROM', 'nobody@fedoraproject.org'),
        smtp_server=APP.config.get('SMTP_SERVER', 'localhost')
    )


def send_lostpassword_email(user):
    """ Sends the email with the information on how to reset his/her password
    to the user.
    """
    url = APP.config.get('APPLICATION_URL', flask.request.url_root)

    message = """ Dear %(username)s,

The IP address %(ip)s has requested a password change for this account.

If you wish to change your password, please click on the following link or
copy/paste it in your browser:
  %(url)s/%(confirm_root)s

If you did not request this change, please inform an admin immediately!

Sincerely,
Your MirrorManager admin.
""" % (
        {
            'username': user.username, 'url': url or flask.request.url_root,
            'confirm_root': flask.url_for('reset_password', token=user.token),
            'ip': flask.request.remote_addr,
        })

    mirrormanager2.lib.notifications.email_publish(
        to_email=user.email_address,
        subject='[MirrorManager] Confirm your password change',
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
            elif APP.config.get('CHECK_SESSION_IP', True) \
                    and session.user_ip != flask.request.remote_addr:
                flask.flash('Session expired', 'error')
            else:
                session_id = session.visit_key
                user = session.user

                session.expiry = new_expiry
                SESSION.add(session)
                try:
                    SESSION.commit()
                except SQLAlchemyError as err:  # pragma: no cover
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
