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

# Set the time after which the session expires. Flask's default is 31 days.
# Default: ``timedelta(hours=1)`` corresponds to 1 hour.
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# url to the database server:
DB_URL = 'sqlite:////var/tmp/mirrormanager2_dev.sqlite'

# the number of items to display on the search pages
# Default: ``50``.
ITEMS_PER_PAGE = 50

# secret key used to generate unique csrf token
SECRET_KEY = '<insert here your own key>'

# Seed used to make the password harder to brute force in case of leaking
# This should be kept really secret!
PASSWORD_SEED = "You'd better change it and keep it secret"

# Folder containing the theme to use.
# Default: ``fedora``.
THEME_FOLDER = 'fedora'

# Which authentication method to use, defaults to `fas` can be or `local`
# Default: ``fas``.
MM_AUTHENTICATION = 'fas'

# If the authentication method is `fas`, groups in which should be the user
# to be recognized as an admin.
ADMIN_GROUP = ('sysadmin-main', )

# Email of the admin to which send notification or error
ADMIN_EMAIL = 'admin@fedoraproject.org'

# Email address used in the 'From' field of the emails sent.
# Default: ``nobody@fedoraproject.org``.
EMAIL_FROM = 'nobody@fedoraproject.org'

# SMTP server to use,
# Default: ``localhost``.
SMTP_SERVER = 'localhost'

# When this is set to True, the session cookie will only be returned to the
# server via ssl (https). If you connect to the server via plain http, the
# cookie will not be sent. This prevents sniffing of the cookie contents.
# This may be set to False when testing your application but should always
# be set to True in production.
# Default: ``True``.
MM_COOKIE_REQUIRES_HTTPS = True

# The name of the cookie used to store the session id.
# Default: ``.MirrorManager``.
MM_COOKIE_NAME = 'MirrorManager'

# If not specified the application will rely on the root_url when sending
# emails, otherwise it will use this URL
# Default: ``None``.
APPLICATION_URL = None

# Boolean specifying wether to check the user's IP address when retrieving
# its session. This make things more secure (thus is on by default) but
# under certain setup it might not work (for example is there are proxies
# in front of the application).
CHECK_SESSION_IP = True

# Specify additional rsync parameters for the crawler
# --timeout 14400: abort rsync crawl after 4 hours
# Depending on the setup and the crawler frequency rsync's timeout option
# can be used decrease the probability of stale rsync processes
CRAWLER_RSYNC_PARAMETERS = '--no-motd --timeout 14400'

# If this variable is set (and the directory exists)
# the crawler will create per host log files with <hostid>.log
# which can the be used in the web interface by the mirror admins
CRAWLER_LOG_DIR = '/var/log/mirrormanager/crawler'
