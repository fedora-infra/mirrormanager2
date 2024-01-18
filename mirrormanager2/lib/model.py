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
MirrorManager2 database model.
"""

import collections
import datetime
import json
import logging
import os
import pickle
import time

import sqlalchemy as sa
from sqlalchemy.orm import deferred, relationship

from .database import BASE

ERROR_LOG = logging.getLogger("mirrormanager2.lib.model")


class Site(BASE):
    __tablename__ = "site"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False)
    password = sa.Column(sa.Text(), default=None, nullable=True)
    org_url = sa.Column(sa.Text(), default=None, nullable=True)
    private = sa.Column(sa.Boolean(), default=False, nullable=False)
    admin_active = sa.Column(sa.Boolean(), default=True, nullable=False)
    user_active = sa.Column(sa.Boolean(), default=True, nullable=False)
    created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    created_by = sa.Column(sa.Text(), nullable=False)
    # allow all sites to pull from me
    all_sites_can_pull_from_me = sa.Column(sa.Boolean(), default=False, nullable=False)
    downstream_comments = sa.Column(sa.Text(), default=None, nullable=True)
    email_on_drop = sa.Column(sa.Boolean(), default=False, nullable=False)
    email_on_add = sa.Column(sa.Boolean(), default=False, nullable=False)

    hosts = relationship(
        "Host",
        back_populates="site",
        cascade="delete, delete-orphan",
    )
    admins = relationship(
        "SiteAdmin",
        back_populates="site",
        cascade="delete, delete-orphan",
    )

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<Site({self.id} - {self.name})>"


class Country(BASE):
    __tablename__ = "country"

    id = sa.Column(sa.Integer, primary_key=True)
    code = sa.Column(sa.Text(), nullable=False, unique=True)
    # hosts = SQLRelatedJoin('Host')


class Host(BASE):
    __tablename__ = "host"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False)
    site_id = sa.Column(sa.Integer, sa.ForeignKey("site.id"), nullable=True)
    robot_email = sa.Column(sa.Text(), nullable=True)
    admin_active = sa.Column(sa.Boolean(), default=True, nullable=False)
    user_active = sa.Column(sa.Boolean(), default=True, nullable=False)
    country = sa.Column(sa.Text(), nullable=False)
    bandwidth_int = sa.Column(sa.Integer, default=100, nullable=True)
    comment = sa.Column(sa.Text(), nullable=True)
    config = deferred(sa.Column(sa.PickleType(), nullable=True))
    last_checked_in = sa.Column(sa.DateTime, nullable=True, default=None)
    last_crawled = sa.Column(sa.DateTime, nullable=True, default=None)
    private = sa.Column(sa.Boolean(), default=False, nullable=False)
    internet2 = sa.Column(sa.Boolean(), default=False, nullable=False)
    internet2_clients = sa.Column(sa.Boolean(), default=False, nullable=False)
    asn = sa.Column(sa.Integer, default=None, nullable=True)
    asn_clients = sa.Column(sa.Boolean(), default=True, nullable=False)
    max_connections = sa.Column(sa.Integer, default=1, nullable=False)
    last_crawl_duration = sa.Column(sa.BigInteger, default=0, nullable=True)
    # Count the last consecutive crawl failures.
    # This can be used to auto disable a host if the crawler fails
    # multiple times in a row.
    crawl_failures = deferred(sa.Column(sa.Integer, default=0, nullable=False))
    # Add a text field to specify why the mirror was disabled.
    # This can either be filled by the crawler for auto disable due
    # to crawl failures, or by an admin (e.g., ticket number)
    disable_reason = deferred(sa.Column(sa.Text(), nullable=True))
    # If SSH based push mirroring will ever be implemented
    # this field should contain the private key to connect to the
    # destination host
    push_ssh_private_key = deferred(sa.Column(sa.Text(), nullable=True))
    # The host to contact for push mirroring
    push_ssh_host = deferred(sa.Column(sa.Text(), nullable=True))
    # The command to execute on the destination host for push mirroring
    push_ssh_command = deferred(sa.Column(sa.Text(), nullable=True))
    # This field holds information about the last few crawls.
    # Which protocols were used, crawl duration, ...
    last_crawls = deferred(sa.Column(sa.PickleType(), nullable=True))

    # Relations
    site = relationship("Site", back_populates="hosts")
    categories = relationship(
        "HostCategory",
        back_populates="host",
        cascade="delete, delete-orphan",
    )
    acl_ips = relationship(
        "HostAclIp",
        back_populates="host",
        cascade="delete, delete-orphan",
    )
    countries_allowed = relationship(
        "HostCountryAllowed",
        back_populates="host",
        cascade="delete, delete-orphan",
    )
    netblocks = relationship(
        "HostNetblock",
        back_populates="host",
        cascade="delete, delete-orphan",
        order_by="HostNetblock.netblock",
    )
    peer_asns = relationship(
        "HostPeerAsn",
        back_populates="host",
        cascade="delete, delete-orphan",
    )
    locations = relationship(
        "HostLocation",
        back_populates="host",
        cascade="delete, delete-orphan",
    )
    countries = relationship(
        "HostCountry",
        back_populates="host",
        cascade="delete, delete-orphan",
    )

    # exclusive_dirs = MultipleJoin('DirectoryExclusiveHost')
    # locations = SQLRelatedJoin('Location')
    # countries = SQLRelatedJoin('Country')

    # Constraints
    __table_args__ = (sa.UniqueConstraint("site_id", "name", name="host_idx"),)

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<Host({self.id} - {self.name})>"

    def __json__(self):
        return dict(
            id=self.id,
            name=self.name,
            site=dict(
                id=self.site.id,
                name=self.site.name,
            ),
            admin_active=self.admin_active,
            user_active=self.user_active,
            country=self.country,
            bandwidth_int=self.bandwidth_int,
            comment=self.comment,
            last_checked_in=self.last_checked_in,
            last_crawled=self.last_crawled,
            private=self.private,
            internet2=self.internet2,
            internet2_clients=self.internet2_clients,
            asn=self.asn,
            asn_clients=self.asn_clients,
            max_connections=self.max_connections,
            last_crawl_duration=self.last_crawl_duration,
        )

    def set_not_up2date(self, session):
        for hc in self.categories:
            for hcd in hc.directories:
                hcd.up2date = False
        session.commit()

    def is_active(self):
        return self.admin_active and self.user_active and self.site.user_active


class JsonDictTypeFilter(sa.types.TypeDecorator):
    """This handles either JSON or a pickled dict from the database."""

    impl = sa.types.BLOB

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        result = []

        for i in list(value.keys()):
            temp = {}
            temp["name"] = i
            temp["size"] = int(value[i]["size"])
            temp["timestamp"] = int(value[i]["stat"])
            result.append(temp)

        return json.dumps(result).encode()

    def process_result_value(self, value, dialect):
        result = {}
        if value is None:
            return result
        try:
            j = json.loads(value)
            for i in j:
                result[i["name"]] = {"size": i["size"], "stat": i["timestamp"]}
        except ValueError:
            result = pickle.loads(value)

        return result


class Directory(BASE):
    __tablename__ = "directory"

    id = sa.Column(sa.Integer, primary_key=True)
    # Full path
    # e.g. pub/epel
    # e.g. pub/fedora/linux
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    files = sa.Column(JsonDictTypeFilter(), nullable=True)
    readable = sa.Column(sa.Boolean(), default=True, nullable=False)
    ctime = sa.Column(sa.BigInteger, default=0, nullable=True)

    host_category_dirs = relationship(
        "HostCategoryDir",
        back_populates="directory",
        cascade="delete, delete-orphan",
    )
    categories = relationship(
        "Category",
        secondary="category_directory",
        back_populates="directories",
        # cascade="delete, delete-orphan",
    )
    categorydir = relationship(
        "CategoryDirectory",
        back_populates="directory",
        cascade="delete, delete-orphan",
        overlaps="categories",
    )
    repositories = relationship(
        "Repository",
        back_populates="directory",
    )
    fileDetails = relationship(
        "FileDetail",
        back_populates="directory",
        cascade="delete, delete-orphan",
    )

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<Directory({self.id} - {self.name})>"

    @classmethod
    def age_file_details(cls, session, config):
        cls._fill_file_details_cache(session, config)
        cls._age_file_details(session, config)

    @classmethod
    def _fill_file_details_cache(cls, session, config):
        cache = collections.defaultdict(list)

        sql = sa.text(
            "SELECT id, directory_id, filename, timestamp from file_detail "
            "ORDER BY directory_id, filename, -timestamp"
        )
        results = session.execute(sql)

        for id, directory_id, filename, timestamp in results:
            k = (directory_id, filename)
            v = dict(file_detail_id=id, timestamp=timestamp)
            cache[k].append(v)

        cls.file_details_cache = cache

    @classmethod
    def _age_file_details(cls, session, config):
        """For each file, keep at least 1 FileDetail entry.

        Remove the second-most recent entry if the most recent entry is
        older than max_propogation_days.  This gives mirrors time to pick
        up the most recent change.

        Remove any others that are more than max_stale_days old.
        """

        t = int(time.time())
        max_stale = config.get("mirrormanager.max_stale_days", 3)
        max_propogation = config.get("mirrormanager.max_propogation_days", 2)
        stale = t - (60 * 60 * 24 * max_stale)
        propogation = t - (60 * 60 * 24 * max_propogation)

        for k, fds in list(cls.file_details_cache.items()):
            (directory_id, filename) = k
            if len(fds) > 1:
                start = 2
                # second-most recent only if most recent has had time to
                # propogate
                if fds[0]["timestamp"] < propogation:
                    start = 1
                # all others
                for f in fds[start:]:
                    if f["timestamp"] < stale:
                        detail = FileDetail.get_by_pk(f["file_detail_id"])
                        session.delete(detail)

        session.commit()


# e.g. 'fedora' and 'epel'
class Product(BASE):
    __tablename__ = "product"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    publiclist = sa.Column(sa.Boolean(), default=True, nullable=False)

    categories = relationship("Category", back_populates="product")
    versions = relationship("Version", back_populates="product")

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<Product({self.id} - {self.name})>"

    @property
    def displayed_versions(self):
        versions = {}
        for version in self.versions:
            if version.display:
                versions[version.name] = version

        # Try to "smartly" sort versions for display.
        # Return a tuple for sorting to avoid str↔int comparisons under python3
        def intify(item):
            k, v = item
            try:
                return (0, int(k))
            except ValueError:
                return (1, k)

        return [v for k, v in sorted(list(versions.items()), reverse=True, key=intify)]


class Category(BASE):
    __tablename__ = "category"

    id = sa.Column(sa.Integer, primary_key=True)
    # Top-level mirroring
    # e.g. 'Fedora Linux', 'Fedora Archive'
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    canonicalhost = sa.Column(sa.Text(), nullable=True, default="http://download.fedora.redhat.com")
    publiclist = sa.Column(sa.Boolean(), default=True, nullable=False)
    geo_dns_domain = sa.Column(sa.Text(), nullable=True)
    admin_only = sa.Column(sa.Boolean(), default=False, nullable=True)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("product.id"), nullable=True)
    topdir_id = sa.Column(sa.Integer, sa.ForeignKey("directory.id"), nullable=True)

    # Relations
    product = relationship("Product", back_populates="categories")
    topdir = relationship("Directory")
    host_categories = relationship("HostCategory", cascade="delete, delete-orphan")
    repositories = relationship("Repository", back_populates="category")
    categorydir = relationship(
        "CategoryDirectory",
        back_populates="category",
        cascade="delete, delete-orphan",
        overlaps="categories",
    )
    # all the directories that are part of this category
    directories = relationship(
        "Directory",
        secondary="category_directory",
        # primaryjoin="category.c.id==category_directory.c.category_id",
        # secondaryjoin="category_directory.c.directory_id==directory.c.id",
        back_populates="categories",
        # cascade="delete, delete-orphan",
        overlaps="categorydir",
    )

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<Category({self.id} - {self.name})>"


class SiteToSite(BASE):
    __tablename__ = "site_to_site"

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.Text(), default=None, nullable=True)
    password = sa.Column(sa.Text(), default=None, nullable=True)
    upstream_site_id = sa.Column(sa.Integer, sa.ForeignKey("site.id"), nullable=False)
    downstream_site_id = sa.Column(sa.Integer, sa.ForeignKey("site.id"), nullable=False)

    # Relations
    upstream_site = relationship("Site", foreign_keys=[upstream_site_id])
    downstream_site = relationship("Site", foreign_keys=[downstream_site_id])

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint("upstream_site_id", "downstream_site_id", name="site_to_site_idx"),
        sa.UniqueConstraint("upstream_site_id", "username", name="site_to_site_username_idx"),
    )


class SiteAdmin(BASE):
    __tablename__ = "site_admin"

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.Text(), default=None, nullable=True)
    site_id = sa.Column(sa.Integer, sa.ForeignKey("site.id"), nullable=False)

    # Relation
    site = relationship(
        "Site",
        back_populates="admins",
    )


class HostCategory(BASE):
    __tablename__ = "host_category"

    id = sa.Column(sa.Integer, primary_key=True)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=True)
    category_id = sa.Column(
        sa.Integer, sa.ForeignKey("category.id", ondelete="CASCADE"), nullable=True
    )
    always_up2date = sa.Column(sa.Boolean(), default=False, nullable=False)

    # Relations
    category = relationship("Category", back_populates="host_categories")
    host = relationship("Host", back_populates="categories")
    directories = relationship(
        "HostCategoryDir",
        back_populates="host_category",
        cascade="delete, delete-orphan",
        order_by="HostCategoryDir.path",
    )
    urls = relationship(
        "HostCategoryUrl",
        back_populates="host_category",
        cascade="delete, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint("host_id", "category_id", name="host_category_hcindex"),
        sa.Index("t_hostcategory_host_id_idx", "host_id"),
        sa.Index("t_hostcategory_category_id_idx", "category_id"),
    )

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<HostCategory({self.id} - {self.category})>"


class HostCategoryDir(BASE):
    __tablename__ = "host_category_dir"

    id = sa.Column(sa.Integer, primary_key=True)
    host_category_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("host_category.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    # subset of the path starting below HostCategory.path
    path = sa.Column(sa.Text(), nullable=True)
    up2date = sa.Column(sa.Boolean, default=True, nullable=False, index=True)
    directory_id = sa.Column(
        sa.Integer, sa.ForeignKey("directory.id", ondelete="CASCADE"), nullable=True
    )

    __mapper_args__ = {"confirm_deleted_rows": False}

    # Relations
    directory = relationship("Directory", back_populates="host_category_dirs")
    host_category = relationship("HostCategory", back_populates="directories")

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint("host_category_id", "path", name="host_category_dir_hcdindex"),
    )


class CategoryDirectory(BASE):
    __tablename__ = "category_directory"

    category_id = sa.Column(sa.Integer, sa.ForeignKey("category.id"), primary_key=True)
    directory_id = sa.Column(sa.Integer, sa.ForeignKey("directory.id"), primary_key=True)
    category = relationship(
        "Category",
        back_populates="categorydir",
        overlaps="categories,directories",
    )
    directory = relationship(
        "Directory",
        back_populates="categorydir",
        overlaps="categories,directories",
    )

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<CategoryDirectory({self.category_id} - {self.directory_id})>"


class HostCategoryUrl(BASE):
    __tablename__ = "host_category_url"

    id = sa.Column(sa.Integer, primary_key=True)
    host_category_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("host_category.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    url = sa.Column(sa.Text(), nullable=False, unique=True)
    private = sa.Column(sa.Boolean(), default=False, nullable=False)

    __mapper_args__ = {"confirm_deleted_rows": False}

    # Relations
    host_category = relationship("HostCategory", back_populates="urls")

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint("host_category_id", "url", name="host_category_url_hcdindex"),
    )


class HostAclIp(BASE):
    __tablename__ = "host_acl_ip"

    id = sa.Column(sa.Integer, primary_key=True)
    ip = sa.Column(sa.Text(), nullable=True, unique=True)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=True)

    # Relation
    host = relationship("Host", back_populates="acl_ips")

    # Constraints
    __table_args__ = (sa.UniqueConstraint("host_id", "ip", name="host_acl_ip_hipindex"),)


class HostCountryAllowed(BASE):
    __tablename__ = "host_country_allowed"

    id = sa.Column(sa.Integer, primary_key=True)
    country = sa.Column(sa.Text(), nullable=False, unique=True)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=True)

    # Relation
    host = relationship("Host", back_populates="countries_allowed")


class HostNetblock(BASE):
    __tablename__ = "host_netblock"

    id = sa.Column(sa.Integer, primary_key=True)
    netblock = sa.Column(sa.Text(), nullable=True)
    name = sa.Column(sa.Text(), nullable=True)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=True)

    # Relation
    host = relationship("Host", back_populates="netblocks")


class HostPeerAsn(BASE):
    __tablename__ = "host_peer_asn"

    id = sa.Column(sa.Integer, primary_key=True)
    asn = sa.Column(sa.Integer, nullable=False)
    name = sa.Column(sa.Text(), nullable=True)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=True)

    # Relation
    host = relationship("Host", back_populates="peer_asns")

    # Constraints
    __table_args__ = (sa.UniqueConstraint("host_id", "asn", name="host_peer_asn_idx"),)


class HostStats(BASE):
    __tablename__ = "host_stats"

    id = sa.Column(sa.Integer, primary_key=True)
    timestamp = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    type = sa.Column(sa.Text(), nullable=True)
    data = sa.Column(sa.PickleType(), nullable=True)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=True)

    # Relation
    host = relationship("Host")


class Arch(BASE):
    __tablename__ = "arch"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    publiclist = sa.Column(sa.Boolean(), default=True, nullable=False)
    primary_arch = sa.Column(sa.Boolean(), default=True, nullable=False)

    repositories = relationship("Repository", back_populates="arch")

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<Arch({self.id} - {self.name})>"


class Version(BASE):
    __tablename__ = "version"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=True)
    codename = sa.Column(sa.Text(), nullable=True)
    is_test = sa.Column(sa.Boolean(), default=False, nullable=False)
    display = sa.Column(sa.Boolean(), default=True, nullable=False)
    display_name = sa.Column(sa.Text(), nullable=True)
    ordered_mirrorlist = sa.Column(sa.Boolean(), default=True, nullable=False)
    sortorder = sa.Column(sa.Integer, default=0, nullable=False)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("product.id"), nullable=True)

    # Relations
    product = relationship("Product", back_populates="versions")
    repositories = relationship("Repository", back_populates="version")

    # Constraints
    __table_args__ = (sa.UniqueConstraint("name", "product_id", name="version_idx"),)

    def __repr__(self):
        """Return a string representation of the object."""
        return f"<Version({self.id} - {self.name})>"

    @property
    def arches(self):
        """Return a list of arches this Version supports via its
        repositories.
        """
        arches = set()
        for repo in self.repositories:
            arches.add(repo.arch.name)
        return arches


class Repository(BASE):
    __tablename__ = "repository"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)
    prefix = sa.Column(sa.Text(), nullable=True)
    category_id = sa.Column(sa.Integer, sa.ForeignKey("category.id"), nullable=True)
    version_id = sa.Column(sa.Integer, sa.ForeignKey("version.id"), nullable=True)
    arch_id = sa.Column(sa.Integer, sa.ForeignKey("arch.id"), nullable=True)
    directory_id = sa.Column(sa.Integer, sa.ForeignKey("directory.id"), nullable=True)
    disabled = sa.Column(sa.Boolean(), default=False, nullable=False)

    # Relations
    category = relationship("Category", back_populates="repositories")
    version = relationship("Version", back_populates="repositories")
    arch = relationship("Arch", back_populates="repositories")
    directory = relationship("Directory", back_populates="repositories")

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint("prefix", "arch_id", name="repository_idx"),
        sa.Index("t_repository_category_id_idx", "category_id"),
        sa.Index("t_repository_version_id_idx", "version_id"),
        sa.Index("t_repository_arch_id_idx", "arch_id"),
        sa.Index("t_repository_directory_id_idx", "directory_id"),
    )

    def emergency_expire_old_file_details(self, session):
        """Emergency method to expire all old files.

        This is to be used to tell clients to only use the newest files.
        CAUTION: this will make all slightly outdated mirrors be non-trusted,
        so should be used sparingly!
        """
        if not self.directory:
            return False

        subdirs = (
            session.query(Directory).filter(Directory.name.like(self.directory.name + "%")).all()
        )

        files_deleted = {}
        for directory in subdirs:
            files = (
                session.query(FileDetail)
                .filter_by(directory_id=directory.id)
                .order_by(FileDetail.timestamp.desc())
                .all()
            )

            for f in files:
                full_filename = os.path.join(directory.name, f.filename)
                if full_filename in files_deleted:
                    files_deleted[full_filename] += 1
                    session.delete(f)
                else:
                    files_deleted[full_filename] = 0

        session.commit()

        return files_deleted


class FileDetail(BASE):
    __tablename__ = "file_detail"

    id = sa.Column(sa.Integer, primary_key=True)
    filename = sa.Column(sa.Text(), nullable=False)
    timestamp = sa.Column(sa.BigInteger, default=None, nullable=True)
    size = sa.Column(sa.BigInteger, default=None, nullable=True)
    sha1 = sa.Column(sa.Text(), nullable=True)
    md5 = sa.Column(sa.Text(), nullable=True)
    sha256 = sa.Column(sa.Text(), nullable=True)
    sha512 = sa.Column(sa.Text(), nullable=True)
    directory_id = sa.Column(sa.Integer, sa.ForeignKey("directory.id"), nullable=False)

    # Relations
    directory = relationship("Directory", back_populates="fileDetails")
    fileGroups = relationship(
        "FileGroup",
        back_populates="files",
        secondary="file_detail_file_group",
    )


class RepositoryRedirect(BASE):
    __tablename__ = "repository_redirect"

    # Uses strings to allow for effective named aliases, and for repos
    # that may not exist yet
    id = sa.Column(sa.Integer, primary_key=True)
    to_repo = sa.Column(sa.Text(), nullable=True)
    from_repo = sa.Column(sa.Text(), nullable=False, unique=True)

    # Constraints
    __table_args__ = (sa.UniqueConstraint("from_repo", "to_repo", name="repository_redirect_idx"),)


class CountryContinentRedirect(BASE):
    __tablename__ = "country_continent_redirect"

    id = sa.Column(sa.Integer, primary_key=True)
    country = sa.Column(sa.Text(), nullable=False, unique=True)
    continent = sa.Column(sa.Text(), nullable=False)


class EmbargoedCountry(BASE):
    __tablename__ = "embargoed_country"

    id = sa.Column(sa.Integer, primary_key=True)
    country_code = sa.Column(sa.Text(), nullable=False, unique=True)


class DirectoryExclusiveHost(BASE):
    __tablename__ = "directory_exclusive_host"

    id = sa.Column(sa.Integer, primary_key=True)
    directory_id = sa.Column(sa.Integer, sa.ForeignKey("directory.id"), nullable=False)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=False)

    # Relations
    directory = relationship("Directory")
    host = relationship("Host")

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint("directory_id", "host_id", name="directory_exclusive_host_idx"),
    )


class Location(BASE):
    """For grouping hosts, perhaps across Site boundaries.  User queries
    may request hosts from a particular Location (such as an Amazon region),
    which will be returned first in the mirror list."""

    __tablename__ = "location"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)

    # hosts = SQLRelatedJoin('Host')


# manual creation of the RelatedJoin table so we can guarantee uniqueness
class HostLocation(BASE):
    __tablename__ = "host_location"

    id = sa.Column(sa.Integer, primary_key=True)
    location_id = sa.Column(sa.Integer, sa.ForeignKey("location.id"), nullable=False)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=False)

    # Relations
    host = relationship("Host", back_populates="locations")
    location = relationship("Location")

    # Constraints
    __table_args__ = (sa.UniqueConstraint("location_id", "host_id", name="host_location_hlidx"),)


class FileGroup(BASE):
    __tablename__ = "file_group"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)

    # all the files related to this group
    files = relationship(
        "FileDetail",
        secondary="file_detail_file_group",
        # primaryjoin="file_detail.c.id==file_detail_file_group.c.file_detail_id",
        # secondaryjoin="file_detail_file_group.c.file_group_id==file_group.c.id",
        back_populates="fileGroups",
    )


class FileDetailFileGroup(BASE):
    __tablename__ = "file_detail_file_group"

    id = sa.Column(sa.Integer, primary_key=True)
    file_detail_id = sa.Column(sa.Integer, sa.ForeignKey("file_detail.id"), nullable=False)
    file_group_id = sa.Column(sa.Integer, sa.ForeignKey("file_group.id"), nullable=False)


class HostCountry(BASE):
    __tablename__ = "host_country"

    id = sa.Column(sa.Integer, primary_key=True)
    country_id = sa.Column(sa.Integer, sa.ForeignKey("country.id"), nullable=False)
    host_id = sa.Column(sa.Integer, sa.ForeignKey("host.id"), nullable=False)

    # Relations
    host = relationship("Host", back_populates="countries")
    country = relationship("Country")

    # Constraints
    __table_args__ = (sa.UniqueConstraint("host_id", "country_id", name="host_country_hlidx"),)


class NetblockCountry(BASE):
    __tablename__ = "netblock_country"

    id = sa.Column(sa.Integer, primary_key=True)
    netblock = sa.Column(sa.Text(), nullable=False, unique=True)
    country = sa.Column(sa.Text(), nullable=False)


# ##########################################################
# These classes are only used if you're using the `local` authentication
# method
class UserVisit(BASE):
    __tablename__ = "mm_user_visit"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("mm_user.id"), nullable=False)
    visit_key = sa.Column(sa.String(40), nullable=False, unique=True, index=True)
    user_ip = sa.Column(sa.String(50), nullable=False)
    created = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    expiry = sa.Column(sa.DateTime)

    user = relationship("User", back_populates="session")


class Group(BASE):
    """
    An ultra-simple group definition.
    """

    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    __tablename__ = "mm_group"

    id = sa.Column(sa.Integer, primary_key=True)
    group_name = sa.Column(sa.String(16), nullable=False, unique=True)
    display_name = sa.Column(sa.String(255), nullable=True)
    created = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)

    users = relationship("User", secondary="mm_user_group", back_populates="group_objs")

    def __repr__(self):
        """Return a string representation of this object."""

        return f"Group: {self.id} - name {self.group_name}"

    # collection of all permissions for this group
    # permissions = RelatedJoin("Permission", joinColumn="group_id",
    # intermediateTable="group_permission",
    # otherColumn="permission_id")


class UserGroup(BASE):
    """
    Association table linking the mm_user table to the mm_group table.
    This allow linking users to groups.
    """

    __tablename__ = "mm_user_group"

    user_id = sa.Column(sa.Integer, sa.ForeignKey("mm_user.id"), primary_key=True)
    group_id = sa.Column(sa.Integer, sa.ForeignKey("mm_group.id"), primary_key=True)

    # Constraints
    __table_args__ = (sa.UniqueConstraint("user_id", "group_id"),)


class User(BASE):
    """
    Reasonably basic User definition. Probably would want additional
    attributes.
    """

    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    __tablename__ = "mm_user"

    id = sa.Column(sa.Integer, primary_key=True)
    user_name = sa.Column(sa.String(16), nullable=False, unique=True)
    email_address = sa.Column(sa.String(255), nullable=False, unique=True)
    display_name = sa.Column(sa.String(255), nullable=True)
    password = sa.Column(sa.Text, nullable=True)
    token = sa.Column(sa.String(50), nullable=True)
    created = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())
    updated_on = sa.Column(
        sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()
    )

    # Relations
    group_objs = relationship(
        "Group",
        secondary="mm_user_group",
        # primaryjoin="mm_user.c.id==mm_user_group.c.user_id",
        # secondaryjoin="mm_group.c.id==mm_user_group.c.group_id",
        back_populates="users",
    )
    session = relationship("UserVisit", back_populates="user")

    @property
    def username(self):
        """Return the username."""
        return self.user_name

    @property
    def groups(self):
        """Return the list of Group.group_name in which the user is."""
        return [group.group_name for group in self.group_objs]

    def __repr__(self):
        """Return a string representation of this object."""

        return f"User: {self.id} - name {self.user_name}"


class AccessStatCategory(BASE):
    """Mirror access statistics category"""

    __tablename__ = "access_stat_category"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False, unique=True)

    access_stats = relationship("AccessStat", back_populates="category")


class AccessStat(BASE):
    """Mirror access statistics"""

    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    __tablename__ = "access_stat"

    category_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("access_stat_category.id"),
        nullable=False,
        primary_key=True,
        index=True,
    )
    date = sa.Column(sa.Date, nullable=False, primary_key=True, index=True)
    name = sa.Column(sa.String(255), nullable=False, primary_key=True)
    percent = sa.Column(sa.Float)
    requests = sa.Column(sa.Integer)

    category = relationship("AccessStatCategory", back_populates="access_stats")
