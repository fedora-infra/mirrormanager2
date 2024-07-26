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
MirrorManager2 notification code.

These methods are used to send email or fedora-messaging message or
any other notifications we could use.
"""


import smtplib
from email.mime.text import MIMEText

import backoff
from fedora_messaging.api import publish as fm_publish
from fedora_messaging.exceptions import ConnectionException, PublishTimeout
from fedora_messaging.message import Message


@backoff.on_exception(
    backoff.expo,
    (ConnectionException, PublishTimeout),
    max_tries=3,
)
def fedmsg_publish(msg: Message):  # pragma: no cover
    """Try to publish a message on the fedmsg bus."""
    fm_publish(msg)


def email_publish(
    to_email,
    subject,
    message,
    from_email="nobody@fedoraproject.org",
    smtp_server="localhost",
):  # pragma: no cover
    """Send notification by email."""

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    smtp = smtplib.SMTP(smtp_server)
    smtp.sendmail(from_email, [to_email], msg.as_string())
    smtp.quit()
