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
MirrorManager2 forms.
'''

# # pylint cannot import flask extension correctly
# pylint: disable=E0611,F0401
# # The forms here don't have specific methods, they just inherit them.
# pylint: disable=R0903
# # We apparently use old style super in our __init__
# pylint: disable=E1002
# # Couple of our forms do not even have __init__
# pylint: disable=W0232


from flask.ext import wtf
import wtforms


def is_number(form, field):
    ''' Check if the data in the field is a number and raise an exception
    if it is not.
    '''
    try:
        float(field.data)
    except ValueError:
        raise wtf.ValidationError('Field must contain a number')


def same_password(form, field):
    ''' Check if the data in the field is the same as in the password field.
    '''
    if field.data != form.password.data:
        raise wtf.ValidationError('Both password fields should be equal')


class AddSiteForm(wtf.Form):
    """ Form to add or edit a site. """
    name = wtforms.TextField(
        'Site name',
        [wtforms.validators.Required()]
    )
    password = wtforms.TextField(
        'Site Password',
        [wtforms.validators.Required()]
    )
    org_url = wtforms.TextField(
        'Organisation URL',
        [wtforms.validators.Required()],
    )
    private = wtforms.BooleanField(
        'Private',
        default=False
    )
    admin_active = wtforms.BooleanField(
        'Admin active',
        default=True
    )
    user_active = wtforms.BooleanField(
        'User active',
        default=True
    )
    all_sites_can_pull_from_me = wtforms.BooleanField(
        'All sites can pull from me?',
        default=False
    )
    downstream_comments = wtforms.TextAreaField(
        'Comments for downstream siteadmins',
    )


class AddHostForm(wtf.Form):
    """ Form to add or edit a host. """
    name = wtforms.TextField(
        'Site name  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    admin_active = wtforms.BooleanField(
        'Admin active',
        default=True
    )
    user_active = wtforms.BooleanField(
        'User active',
        default=True
    )
    country = wtforms.TextField(
        'Country  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    bandwidth_int = wtforms.TextField(
        'Bandwidth  <span class="error">*</span>',
        [wtforms.validators.Required(), is_number],
    )
    private = wtforms.BooleanField(
        'Private',
        default=False
    )

    internet2 = wtforms.BooleanField(
        'Internet2',
        default=False
    )
    internet2_clients = wtforms.BooleanField(
        'Internet2 clients',
        default=False
    )
    asn = wtforms.TextField(
        'ASN',
        [wtforms.validators.Optional(), is_number],
    )
    asn_clients = wtforms.BooleanField(
        'ASN Clients?',
        default=True
    )
    robot_email = wtforms.TextField(
        'Robot email',
        [wtforms.validators.Optional()],
    )
    comment = wtforms.TextField(
        'Bandwidth',
        [wtforms.validators.Optional()],
    )
    max_connections = wtforms.TextField(
        'Max connections  <span class="error">*</span>',
        [wtforms.validators.Required(), is_number],
        default=1
    )


class AddHostAclIpForm(wtf.Form):
    """ Form to add or edit a host_acl_ip. """
    ip = wtforms.TextField(
        'IP  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )


class AddHostNetblockForm(wtf.Form):
    """ Form to add or edit a host_netblock. """
    name = wtforms.TextField(
        'Name  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    netblock = wtforms.TextField(
        'Netblock  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )


class AddHostAsnForm(wtf.Form):
    """ Form to add or edit a host_peer_asn. """
    name = wtforms.TextField(
        'Name  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    asn = wtforms.TextField(
        'ASN  <span class="error">*</span>',
        [wtforms.validators.Required(), is_number]
    )


class AddHostCountryForm(wtf.Form):
    """ Form to add or edit a host_country. """
    country = wtforms.TextField(
        'Country  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )


class AddHostCategoryForm(wtf.Form):
    """ Form to add a host_category. """
    category_id = wtforms.SelectField(
        'Category',
        [wtforms.validators.Required(), is_number],
        choices=[(item, item) for item in []]
    )
    always_up2date = wtforms.BooleanField(
        'Always up to date',
        default=False
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of collection provided to fill the choices of the
        drop-down list.
        """
        super(AddHostCategoryForm, self).__init__(*args, **kwargs)
        if 'categories' in kwargs:
            self.category_id.choices = [
                (cat.id, cat.name)
                for cat in kwargs['categories']
            ]


class EditHostCategoryForm(wtf.Form):
    """ Form to edit a host_category. """
    always_up2date = wtforms.BooleanField(
        'Always up to date',
        default=False
    )


class AddHostCategoryUrlForm(wtf.Form):
    """ Form to add a host_category_url. """
    url = wtforms.TextField(
        'URL  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    private = wtforms.BooleanField(
        'Private',
        default=False,
    )


class LostPasswordForm(wtf.Form):
    """ Form to ask for a password change. """
    username = wtforms.TextField(
        'username  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )


class ResetPasswordForm(wtf.Form):
    """ Form to reset one's password in the local database. """
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    confirm_password = wtforms.PasswordField(
        'Confirm password  <span class="error">*</span>',
        [wtforms.validators.Required(), same_password]
    )


class LoginForm(wtf.Form):
    """ Form to login via the local database. """
    username = wtforms.TextField(
        'username  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )


class NewUserForm(wtf.Form):
    """ Form to add a new user to the local database. """
    user_name = wtforms.TextField(
        'username  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    display_name = wtforms.TextField(
        'Full name',
        [wtforms.validators.Optional()]
    )
    email_address = wtforms.TextField(
        'Email address  <span class="error">*</span>',
        [wtforms.validators.Required(), wtforms.validators.Email()]
    )
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    confirm_password = wtforms.PasswordField(
        'Confirm password  <span class="error">*</span>',
        [wtforms.validators.Required(), same_password]
    )
