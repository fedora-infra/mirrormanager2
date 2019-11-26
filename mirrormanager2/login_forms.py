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
MirrorManager2 login forms.
'''

# # pylint cannot import flask extension correctly
# pylint: disable=E0611,F0401
# # The forms here don't have specific methods, they just inherit them.
# pylint: disable=R0903
# # We apparently use old style super in our __init__
# pylint: disable=E1002
# # Couple of our forms do not even have __init__
# pylint: disable=W0232


import flask_wtf as wtf
import wtforms
try:
    from flask_wtf import FlaskForm
except ImportError:
    from flask_wtf import Form as FlaskForm


def same_password(form, field):
    ''' Check if the data in the field is the same as in the password field.
    '''
    if field.data != form.password.data:
        raise wtf.ValidationError('Both password fields should be equal')


class LostPasswordForm(FlaskForm):
    """ Form to ask for a password change. """
    username = wtforms.StringField(
        'username  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )


class ResetPasswordForm(FlaskForm):
    """ Form to reset one's password in the local database. """
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )
    confirm_password = wtforms.PasswordField(
        'Confirm password  <span class="error">*</span>',
        [wtforms.validators.InputRequired(), same_password]
    )


class LoginForm(FlaskForm):
    """ Form to login via the local database. """
    username = wtforms.StringField(
        'username  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )


class NewUserForm(FlaskForm):
    """ Form to add a new user to the local database. """
    user_name = wtforms.StringField(
        'username  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )
    display_name = wtforms.StringField(
        'Full name',
        [wtforms.validators.Optional()]
    )
    email_address = wtforms.StringField(
        'Email address  <span class="error">*</span>',
        [wtforms.validators.InputRequired(), wtforms.validators.Email()]
    )
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )
    confirm_password = wtforms.PasswordField(
        'Confirm password  <span class="error">*</span>',
        [wtforms.validators.InputRequired(), same_password]
    )
