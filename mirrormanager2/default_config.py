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
MirrorManager2 default configuration api.
'''

from datetime import timedelta

# Set the time after which the session expires
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# url to the database server:
DB_URL = 'sqlite:////var/tmp/mirrormanager2_dev.sqlite'

# the number of items to display on the search pages
ITEMS_PER_PAGE = 50

# secret key used to generate unique csrf token
SECRET_KEY = '<insert here your own key>'

# Folder containing the theme to use, defaults to the Fedora theme
THEME_FOLDER = 'fedora'

# Which authentication method to use, defaults to `fas` can be or `local`
MM_AUTHENTICATION = 'fas'

# If the authentication method is `fas`, groups in which should be the user
# to be recognized as an admin.
ADMIN_GROUP = ('sysadmin-main', )
