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

"""
MirrorManager2 default configuration api.
"""

import os
from datetime import timedelta

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Set the time after which the session expires. Flask's default is 31 days.
# Default: ``timedelta(hours=1)`` corresponds to 1 hour.
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# url to the database server:
SQLALCHEMY_DATABASE_URI = "sqlite:////var/tmp/mirrormanager2_dev.sqlite"
DB_MODELS_LOCATION = "mirrormanager2.lib.model"

DB_ALEMBIC_LOCATION = os.path.join(BASE_PATH, "lib", "migrations")

# the number of items to display on the search pages
# Default: ``20``.
ITEMS_PER_PAGE = 20

# secret key used to generate unique csrf token
SECRET_KEY = "<insert here your own key>"

# Seed used to make the password harder to brute force in case of leaking
# This should be kept really secret!
PASSWORD_SEED = "You'd better change it and keep it secret"

# Folder containing the theme to use.
# Rocky: changed from fedora to rocky
# Source: mirrormanager-rocky/mirrormanager2.cfg line 40
# THEME_FOLDER = os.environ.get('MM2_THEME_FOLDER', 'fedora')
# Source: mirrormanager-rocky/start-dev.sh line 26
# -e 'MM2_THEME_FOLDER=rocky'
THEME_FOLDER = "rocky"

# Which authentication method to use, defaults to `fas` can be or `local`
# Default: ``fas``.
# Note that this previously used openid, now it uses openid connect oidc
MM_AUTHENTICATION = "fas"

OIDC_CLIENT_SECRETS = os.path.join(BASE_PATH, "..", "client_secrets.json")
OIDC_SCOPES = " ".join(
    [
        "openid",
        "email",
        "profile",
        "https://id.fedoraproject.org/scope/groups",
        "https://id.fedoraproject.org/scope/agreements",
    ]
)

# If the authentication method is `fas`, groups in which should be the user
# to be recognized as an admin.
# Rocky: changed from sysadmin-main to infrastructure
# Source: mirrormanager-rocky/mirrormanager2.cfg line 61
# ADMIN_GROUP = ["infrastructure"]
ADMIN_GROUP = ["infrastructure"]

# Email of the admin to which send notification or error
# Rocky: changed from fedoraproject.org to rockylinux.org
# Source: mirrormanager-rocky/mirrormanager2.cfg line 64
# ADMIN_EMAIL = "infrastructure@rockylinux.org"
ADMIN_EMAIL = "infrastructure@rockylinux.org"

# Email address used in the 'From' field of the emails sent.
# Rocky: changed from fedoraproject.org to rockylinux.org
# Source: mirrormanager-rocky/mirrormanager2.cfg line 68
# EMAIL_FROM = "nobody@rockylinux.org"
EMAIL_FROM = "nobody@rockylinux.org"

# SMTP server to use,
# Default: ``localhost``.
SMTP_SERVER = "localhost"

# How long to keep the access stats, in days
ACCESS_STATS_KEEP_DAYS = 30

# Countries which have to be excluded.
# Rocky: added "RU" (Russia) to the list
# Source: mirrormanager-rocky/mirrormanager2.cfg line 76
# EMBARGOED_COUNTRIES = ["CU", "IR", "KP", "SD", "SY", "RU"]
EMBARGOED_COUNTRIES = ["CU", "IR", "KP", "SD", "SY", "RU"]

# When this is set to True, an additional menu item is shown which
# displays the maps generated with mm2_generate-worldmap.
SHOW_MAPS = True

# Location of the static map displayed in the map tab.
STATIC_MAP = "map.png"

# Location of the interactive openstreetmap based map.
INTERACTIVE_MAP = "mirrors.html"

# The crawler can generate propagation statistics which can be
# converted into svg/pdf with mm2_propagation. These files
# can be displayed next to the statistics and maps tab if desired.
SHOW_PROPAGATION = True

# Where to look for the above mentioned propagation images.
PROPAGATION_BASE = "/var/lib/mirrormanager/statistics/data/propagation"

# How long to keep the propagation stats, in days
PROPAGATION_KEEP_DAYS = 7

# Where the GeoIP database lives
GEOIP_BASE = "/usr/share/GeoIP"

# Disable master rsync server ACL
# Fedora does not use it and therefore it is set to False
MASTER_RSYNC_ACL = False

# When this is set to True, the session cookie will only be returned to the
# server via ssl (https). If you connect to the server via plain http, the
# cookie will not be sent. This prevents sniffing of the cookie contents.
# This may be set to False when testing your application but should always
# be set to True in production.
# Default: ``True``.
MM_COOKIE_REQUIRES_HTTPS = True

# The name of the cookie used to store the session id.
# Default: ``.MirrorManager``.
MM_COOKIE_NAME = "MirrorManager"

# If this variable is set (and the directory exists) the crawler
# will create per host log files in MM_LOG_DIR/crawler/<hostid>.log
# which can the be used in the web interface by the mirror admins.
# Other parts besides the crawler are also using this variable to
# decide where to store log files.
MM_LOG_DIR = "/var/log/mirrormanager"

# This is used to exclude certain protocols to be entered
# for host category URLs at all.
# The following is the default for Fedora to exclude FTP based
# mirrors to be added. Removing this confguration option
# or setting it to '' removes any protocol restrictions.
MM_PROTOCOL_REGEX = "^(?!ftp)(.*)$"

# The netblock size parameters define which netblock sizes can be
# added by a site administrator. Larger networks can only be added by
# mirrormanager admins.
MM_IPV4_NETBLOCK_SIZE = "/16"
MM_IPV6_NETBLOCK_SIZE = "/32"

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
# # --timeout 14400: abort rsync crawl after 4 hours
# # --no-human-readable: because rsync made things pretty by default in 3.1.x
CRAWLER_RSYNC_PARAMETERS = "--no-motd"


###
# Configuration options used by the utilities
###

# Specify additional rsync parameters for the crawler
# --timeout 14400: abort rsync crawl after 4 hours
# Depending on the setup and the crawler frequency rsync's timeout option
# can be used decrease the probability of stale rsync processes
CRAWLER_RSYNC_PARAMETERS = "--no-motd --timeout 14400"

# If a host fails for CRAWLER_AUTO_DISABLE times in a row
# the host will be disable automatically (user_active)
CRAWLER_AUTO_DISABLE = 4

# This is a list of directories which MirrorManager will ignore while guessing
# the version and architecture from a path.
SKIP_PATHS_FOR_VERSION = ["pub/alt"]

# To get the current versions
BODHI_URL = "https://bodhi.fedoraproject.org"

# Whether to use Fedora Messaging for notifications
USE_FEDORA_MESSAGING = True

# Maximum age of a FileDetail entry in the database
MAX_STALE_DAYS = 4

UMDL_PREFIX = ""

UMDL_MASTER_DIRECTORIES = []

HEALTHZ = {
    "live": "mirrormanager2.health_checks.liveness",
    "ready": "mirrormanager2.health_checks.readiness",
}
