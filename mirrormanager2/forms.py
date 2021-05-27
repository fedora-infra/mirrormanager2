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


import re
import wtforms
try:
    from flask_wtf import FlaskForm
except ImportError:
    from flask_wtf import Form as FlaskForm

from flask import g

import IPy

from mirrormanager2.app import APP

COUNTRY_REGEX = '^[a-zA-Z][a-zA-Z]$'


def is_number(form, field):
    ''' Check if the data in the field is a number and raise an exception
    if it is not.
    '''
    try:
        float(field.data)
    except ValueError:
        raise wtforms.ValidationError('Field must contain a number')


class ConfirmationForm(FlaskForm):
    """ Simple form, just used for CSRF protection. """
    pass


class AddSiteForm(FlaskForm):
    """ Form to add or edit a site. """
    name = wtforms.StringField(
        'Site name',
        [wtforms.validators.InputRequired()]
    )
    password = wtforms.StringField(
        'Site Password',
        [wtforms.validators.InputRequired()]
    )
    org_url = wtforms.StringField(
        'Organisation URL',
        [wtforms.validators.InputRequired()],
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
    downstream_comments = wtforms.StringField(
        'Comments for downstream siteadmins',
    )


class AddHostForm(FlaskForm):
    """ Form to add or edit a host. """
    name = wtforms.StringField(
        'Host name  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )
    admin_active = wtforms.BooleanField(
        'Admin active',
        default=True
    )
    user_active = wtforms.BooleanField(
        'User active',
        default=True
    )
    disable_reason = wtforms.StringField(
        'Disable Reason',
        [wtforms.validators.Optional()],
    )
    country = wtforms.StringField(
        'Country  <span class="error">*</span>',
        [
            wtforms.validators.InputRequired(),
            wtforms.validators.Regexp(COUNTRY_REGEX, flags=re.IGNORECASE),
        ]
    )
    bandwidth_int = wtforms.StringField(
        'Bandwidth  <span class="error">*</span>',
        [wtforms.validators.InputRequired(), is_number],
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
    asn = wtforms.StringField(
        'ASN',
        [wtforms.validators.Optional(), is_number],
    )
    asn_clients = wtforms.BooleanField(
        'ASN Clients?',
        default=True
    )
    robot_email = wtforms.StringField(
        'Robot email',
        [wtforms.validators.Optional()],
    )
    comment = wtforms.StringField(
        'Comment',
        [wtforms.validators.Optional()],
    )
    max_connections = wtforms.StringField(
        'Max connections  <span class="error">*</span>',
        [wtforms.validators.InputRequired(), is_number],
        default=1
    )


class AddHostAclIpForm(FlaskForm):
    """ Form to add or edit a host_acl_ip. """
    ip = wtforms.StringField(
        'IP  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )

def validate_netblocks(form, field):
    max_ipv4_netblock_size = APP.config.get('MM_IPV4_NETBLOCK_SIZE', '/16')
    max_ipv6_netblock_size = APP.config.get('MM_IPV6_NETBLOCK_SIZE', '/32')

    emsg = "Error: IPv4 netblocks larger than %s" % max_ipv4_netblock_size
    emsg += ", and IPv6 netblocks larger than %s" % max_ipv6_netblock_size
    emsg += " can only be created by mirrormanager administrators."
    emsg += " Please ask the mirrormanager administrators for assistance."

    ipv4_block = IPy.IP('10.0.0.0%s' % max_ipv4_netblock_size)
    ipv6_block = IPy.IP('fec0::%s'   % max_ipv6_netblock_size)

    try:
        ip = IPy.IP(field.data, make_net=True)
    except ValueError:
        # also accept DNS hostnames
        return
    if (((ip.version() == 4 and ip.len() > ipv4_block.len()) or
            (ip.version() == 6 and ip.len() > ipv6_block.len())) and
             not g.is_mirrormanager_admin):
        raise wtforms.validators.ValidationError(emsg)


class AddHostNetblockForm(FlaskForm):
    """ Form to add or edit a host_netblock. """
    name = wtforms.StringField(
        'Name  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )
    netblock = wtforms.StringField(
        'Netblock  <span class="error">*</span>',
        [wtforms.validators.InputRequired(), validate_netblocks]
    )


class AddHostAsnForm(FlaskForm):
    """ Form to add or edit a host_peer_asn. """
    name = wtforms.StringField(
        'Name  <span class="error">*</span>',
        [wtforms.validators.InputRequired()]
    )
    asn = wtforms.StringField(
        'ASN  <span class="error">*</span>',
        [wtforms.validators.InputRequired(), is_number]
    )


class AddHostCountryForm(FlaskForm):
    """ Form to add or edit a host_country. """
    country = wtforms.StringField(
        'Country  <span class="error">*</span>',
        [
            wtforms.validators.InputRequired(),
            wtforms.validators.Regexp(COUNTRY_REGEX, flags=re.IGNORECASE),
        ]
    )


class AddHostCategoryForm(FlaskForm):
    """ Form to add a host_category. """
    category_id = wtforms.SelectField(
        'Category',
        [wtforms.validators.InputRequired(), is_number],
        choices=[(item, item) for item in []],
        coerce=int
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


class EditHostCategoryForm(FlaskForm):
    """ Form to edit a host_category. """
    always_up2date = wtforms.BooleanField(
        'Always up to date',
        default=False
    )


class AddHostCategoryUrlForm(FlaskForm):
    """ Form to add a host_category_url. """
    p = APP.config.get('MM_PROTOCOL_REGEX', '')
    url = wtforms.StringField(
        'URL  <span class="error">*</span>',
        [
            wtforms.validators.InputRequired(),
            # private mirrors might have unusual URLs
            wtforms.validators.URL(require_tld=False),
            wtforms.validators.Regexp(
                p,
                flags=re.IGNORECASE,
                message=u'Unsupported URL'
            ),
        ]
    )
    private = wtforms.BooleanField(
        'Private',
        default=False,
    )
