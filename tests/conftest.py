"""
mirrormanager2 tests.
"""

import datetime
import logging
import os

import pytest
import responses

from mirrormanager2.app import DB, create_app
from mirrormanager2.lib import model

from .auth import AnotherFakeFasUser, FakeFasUser, FakeFasUserAdmin, user_set

HERE = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            # A file database is required to check the integrity, don't ask
            "DB_URL": f"sqlite:///{tmp_path.as_posix()}/test.sqlite",
            "OIDC_CLIENT_SECRETS": os.path.join(HERE, "client_secrets.json"),
            "USE_FEDORA_MESSAGING": False,
        }
    )
    app.logger.handlers = []
    app.logger.setLevel(logging.CRITICAL)
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def mock_oidc():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.get("https://id.example.com/openidc/.well-known/openid-configuration", json={})
        yield rsps


@pytest.fixture()
def db(app):
    model.create_tables(app.config["DB_URL"], debug=False)
    session = DB.session
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def user(client):
    user = FakeFasUser()
    with user_set(client, user):
        yield user


@pytest.fixture()
def admin_user(client):
    user = FakeFasUserAdmin()
    with user_set(client, user):
        yield user


@pytest.fixture()
def another_user(client):
    user = AnotherFakeFasUser()
    with user_set(client, user):
        yield user


@pytest.fixture()
def base_items(db):
    """Insert some base information in the database."""
    # Insert some Arch
    item = model.Arch(
        name="source",
        publiclist=False,
        primary_arch=False,
    )
    db.add(item)
    item = model.Arch(
        name="i386",
        publiclist=True,
        primary_arch=True,
    )
    db.add(item)
    item = model.Arch(
        name="x86_64",
        publiclist=True,
        primary_arch=True,
    )
    db.add(item)
    item = model.Arch(
        name="ppc",
        publiclist=True,
        primary_arch=False,
    )
    db.add(item)

    # Insert some Country
    item = model.Country(
        code="FR",
    )
    db.add(item)
    item = model.Country(
        code="US",
    )
    db.add(item)

    # Insert some Product
    item = model.Product(
        name="EPEL",
        publiclist=True,
    )
    db.add(item)
    item = model.Product(
        name="Fedora",
        publiclist=True,
    )
    db.add(item)

    # Insert some CountryContinentRedirect
    item = model.CountryContinentRedirect(
        country="IL",
        continent="EU",
    )
    db.add(item)
    item = model.CountryContinentRedirect(
        country="AM",
        continent="EU",
    )
    db.add(item)
    item = model.CountryContinentRedirect(
        country="JO",
        continent="EU",
    )
    db.add(item)

    # Insert some User
    item = model.User(
        user_name="pingou",
        email_address="pingou@fp.o",
        display_name="pingou",
        password="foo",
    )
    db.add(item)
    item = model.User(
        user_name="kevin",
        email_address="kevin@fp.o",
        display_name="kevin",
        password="foo2",
    )
    db.add(item)
    item = model.User(
        user_name="ralph",
        email_address="ralph@fp.o",
        display_name="ralph",
        password="foo3",
    )
    db.add(item)
    item = model.User(
        user_name="shaiton",
        email_address="shaiton@fp.o",
        display_name="shaiton",
        password="foo4",
        token="bar",
    )
    db.add(item)

    # Insert some UserVisit
    item = model.UserVisit(
        user_id=1,
        visit_key="foo",
        user_ip="127.0.0.1",
        expiry=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def site(db):
    """Create some site to play with for the tests"""
    item = model.Site(
        name="test-mirror",
        password="test_password",
        org_url="http://fedoraproject.org",
        private=False,
        admin_active=True,
        user_active=True,
        all_sites_can_pull_from_me=True,
        downstream_comments="Mirror available over RSYNC and HTTP.",
        email_on_drop=False,  # Default value - not changeable in the UI Oo
        email_on_add=False,  # Default value - not changeable in the UI Oo
        created_by="pingou",
    )
    db.add(item)
    item = model.Site(
        name="test-mirror2",
        password="test_password2",
        org_url="http://getfedora.org",
        private=False,
        admin_active=True,
        user_active=True,
        all_sites_can_pull_from_me=True,
        downstream_comments="Mirror available over HTTP.",
        email_on_drop=False,
        email_on_add=False,
        created_by="kevin",
    )
    db.add(item)
    item = model.Site(
        name="test-mirror_private",
        password="test_password_private",
        org_url="http://192.168.0.15",
        private=True,
        admin_active=True,
        user_active=True,
        all_sites_can_pull_from_me=False,
        downstream_comments="My own mirror available over HTTP.",
        email_on_drop=False,
        email_on_add=False,
        created_by="skvidal",
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def site_admin(db):
    """Create some site admins to play with for the tests"""
    item = model.SiteAdmin(
        username="ralph",
        site_id=1,
    )
    db.add(item)
    item = model.SiteAdmin(
        username="kevin",
        site_id=1,
    )
    db.add(item)

    item = model.SiteAdmin(
        username="ralph",
        site_id=2,
    )
    db.add(item)
    item = model.SiteAdmin(
        username="pingou",
        site_id=2,
    )
    db.add(item)

    item = model.SiteAdmin(
        username="shaiton",
        site_id=3,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hosts(db):
    """Create some hosts to play with for the tests"""
    item = model.Host(
        name="mirror.localhost",
        site_id=1,
        robot_email=None,
        admin_active=True,
        user_active=True,
        country="US",
        bandwidth_int=100,
        comment=None,
        private=False,
        internet2=False,
        internet2_clients=False,
        asn=None,
        asn_clients=False,
        max_connections=10,
    )
    db.add(item)
    item = model.Host(
        name="mirror2.localhost",
        site_id=2,
        robot_email=None,
        admin_active=True,
        user_active=True,
        country="FR",
        bandwidth_int=100,
        comment=None,
        private=False,
        internet2=False,
        internet2_clients=False,
        asn=100,
        asn_clients=True,
        max_connections=10,
    )
    db.add(item)
    item = model.Host(
        name="private.localhost",
        site_id=1,
        robot_email=None,
        admin_active=True,
        user_active=True,
        country="NL",
        bandwidth_int=100,
        comment="My own private mirror",
        private=True,
        internet2=False,
        internet2_clients=False,
        asn=None,
        asn_clients=False,
        max_connections=10,
    )
    db.add(item)

    db.add(item)
    item = model.Host(
        name="Another test entry",
        site_id=3,
        robot_email=None,
        admin_active=True,
        user_active=True,
        country="HR",
        bandwidth_int=300,
        comment="Public mirror",
        private=False,
        internet2=False,
        internet2_clients=False,
        asn=None,
        asn_clients=False,
        max_connections=10,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def host_country_allowed(db):
    item = model.HostCountryAllowed(
        country="HR",
        host_id=4,
    )
    db.add(item)
    item = model.HostCountryAllowed(
        country="US",
        host_id=4,
    )
    db.add(item)
    db.commit()


@pytest.fixture()
def hostaclip(db):
    """Create some HostAclIp to play with for the tests"""
    item = model.HostAclIp(
        ip="85.12.0.250",
        host_id=1,
    )
    db.add(item)

    item = model.HostAclIp(
        ip="192.168.0.12",
        host_id=2,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def directory(db):
    """Create some Directory to play with for the tests"""
    item = model.Directory(
        name="pub/fedora/linux",
        readable=True,
    )
    db.add(item)

    item = model.Directory(
        name="pub/fedora/linux/extras",
        readable=True,
    )
    db.add(item)

    item = model.Directory(
        name="pub/epel",
        readable=True,
    )
    db.add(item)

    item = model.Directory(
        name="pub/fedora/linux/releases/26",
        readable=True,
    )
    db.add(item)

    item = model.Directory(
        name="pub/fedora/linux/releases/27",
        readable=True,
    )
    db.add(item)

    item = model.Directory(
        name="pub/archive/fedora/linux/releases/26/Everything/source",
        readable=True,
    )
    db.add(item)

    item = model.Directory(
        name="pub/fedora/linux/updates/testing/25/x86_64",
        readable=True,
    )
    db.add(item)
    item = model.Directory(
        name="pub/fedora/linux/updates/testing/26/x86_64",
        readable=True,
    )
    db.add(item)
    item = model.Directory(
        name="pub/fedora/linux/updates/testing/27/x86_64",
        readable=True,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def category(db):
    """Create some Category to play with for the tests"""
    item = model.Category(
        name="Fedora Linux",
        product_id=2,
        canonicalhost="http://download.fedora.redhat.com",
        topdir_id=1,
        publiclist=True,
    )
    db.add(item)

    item = model.Category(
        name="Fedora EPEL",
        product_id=1,
        canonicalhost="http://dl.fedoraproject.org",
        topdir_id=2,
        publiclist=True,
    )
    db.add(item)

    db.commit()

    item = model.Category(
        name="Fedora Codecs",
        product_id=2,
        canonicalhost="http://codecs.fedoraproject.org",
        topdir_id=4,
        publiclist=False,
        admin_only=True,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hostcategory(db):
    """Create some HostCategory to play with for the tests"""
    item = model.HostCategory(
        host_id=1,
        category_id=1,
        always_up2date=True,
    )
    db.add(item)
    item = model.HostCategory(
        host_id=1,
        category_id=2,
        always_up2date=True,
    )
    db.add(item)

    item = model.HostCategory(
        host_id=2,
        category_id=1,
        always_up2date=False,
    )
    db.add(item)
    item = model.HostCategory(
        host_id=2,
        category_id=2,
        always_up2date=False,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hostcategoryurl(db):
    """Create some HostCategoryUrl to play with for the tests"""
    item = model.HostCategoryUrl(
        host_category_id=1,
        url="http://infrastructure.fedoraproject.org/pub/fedora/linux",
        private=False,
    )
    db.add(item)
    item = model.HostCategoryUrl(
        host_category_id=1,
        url="http://infrastructure.fedoraproject.org/pub/epel",
        private=False,
    )
    db.add(item)

    item = model.HostCategoryUrl(
        host_category_id=1,
        url="http://dl.fedoraproject.org/pub/fedora/linux",
        private=False,
    )
    db.add(item)
    item = model.HostCategoryUrl(
        host_category_id=1,
        url="http://dl.fedoraproject.org/pub/epel",
        private=False,
    )
    db.add(item)

    item = model.HostCategoryUrl(
        host_category_id=3,
        url="https://infrastructure.fedoraproject.org/pub/fedora/linux",
        private=False,
    )
    db.add(item)
    item = model.HostCategoryUrl(
        host_category_id=3,
        url="https://infrastructure.fedoraproject.org/pub/epel",
        private=False,
    )
    db.add(item)

    item = model.HostCategoryUrl(
        host_category_id=3,
        url="https://dl.fedoraproject.org/pub/fedora/linux",
        private=False,
    )
    db.add(item)
    item = model.HostCategoryUrl(
        host_category_id=3,
        url="https://dl.fedoraproject.org/pub/epel",
        private=False,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def categorydirectory(db):
    """Create some CategoryDirectory to play with for the tests"""
    item = model.CategoryDirectory(
        directory_id=1,
        category_id=1,
    )
    db.add(item)
    item = model.CategoryDirectory(
        directory_id=4,
        category_id=1,
    )
    db.add(item)
    item = model.CategoryDirectory(
        directory_id=5,
        category_id=1,
    )
    db.add(item)

    item = model.CategoryDirectory(
        directory_id=3,
        category_id=2,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hostnetblock(db):
    """Create some HostNetblock to play with for the tests"""
    item = model.HostNetblock(
        host_id=3,
        netblock="192.168.0.0/24",
        name="home",
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hostpeerasn(db):
    """Create some HostPeerAsn to play with for the tests"""
    item = model.HostPeerAsn(
        host_id=3,
        asn="25640",
        name="Hawaii",
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hostcountry(db):
    """Create some HostCountry to play with for the tests"""
    item = model.HostCountry(
        host_id=1,
        country_id=2,
    )
    db.add(item)
    item = model.HostCountry(
        host_id=2,
        country_id=1,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def version(db):
    """Create some Version to play with for the tests"""
    item = model.Version(
        name=26,
        product_id=2,
        is_test=False,
        display=True,
        ordered_mirrorlist=True,
    )
    db.add(item)
    item = model.Version(
        name="27-alpha",
        product_id=2,
        is_test=True,
        display=False,
        ordered_mirrorlist=True,
    )
    db.add(item)
    item = model.Version(
        name=27,
        product_id=2,
        is_test=False,
        display=True,
        ordered_mirrorlist=True,
    )
    db.add(item)
    item = model.Version(
        name="development",
        product_id=2,
        is_test=False,
        display=True,
        display_name="rawhide",
        ordered_mirrorlist=True,
    )
    db.add(item)
    item = model.Version(
        name=25,
        product_id=2,
        is_test=False,
        display=True,
        ordered_mirrorlist=True,
    )
    db.add(item)

    item = model.Version(
        name=7,
        product_id=1,
        is_test=False,
        display=True,
        ordered_mirrorlist=True,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def repository(db):
    """Create some Repository to play with for the tests"""
    item = model.Repository(
        name="pub/fedora/linux/updates/testing/25/x86_64",
        prefix="updates-testing-f25",
        category_id=1,
        version_id=5,
        arch_id=3,
        directory_id=7,
        disabled=True,
    )
    db.add(item)
    item = model.Repository(
        name="pub/fedora/linux/updates/testing/26/x86_64",
        prefix="updates-testing-f26",
        category_id=1,
        version_id=1,
        arch_id=3,
        directory_id=8,
        disabled=False,
    )
    db.add(item)
    item = model.Repository(
        name="pub/fedora/linux/updates/testing/27/x86_64",
        prefix="updates-testing-f27",
        category_id=1,
        version_id=3,
        arch_id=3,
        directory_id=9,
        disabled=False,
    )
    db.add(item)
    item = model.Repository(
        name="pub/fedora/linux/updates/27/x86_64",
        prefix="updates-released-f27",
        category_id=1,
        version_id=3,
        arch_id=3,
        directory_id=5,
        disabled=False,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def repositoryredirect(db):
    """Create some RepositoryRedirect to play with for the tests"""
    item = model.RepositoryRedirect(
        from_repo="fedora-rawhide",
        to_repo="rawhide",
    )
    db.add(item)
    item = model.RepositoryRedirect(
        from_repo="fedora-install-rawhide",
        to_repo="rawhide",
    )
    db.add(item)
    item = model.RepositoryRedirect(
        from_repo="epel-6.0",
        to_repo="epel-6",
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def location(db):
    """Create some Location to play with for the tests"""
    item = model.Location(
        name="foo",
    )
    db.add(item)
    item = model.Location(
        name="bar",
    )
    db.add(item)
    item = model.Location(
        name="foobar",
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def netblockcountry(db):
    """Create some NetblockCountry to play with for the tests"""
    item = model.NetblockCountry(
        netblock="127.0.0.0/24",
        country="AU",
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hostcategorydir(db):
    """Create some HostCategoryDir to play with for the tests"""
    item = model.HostCategoryDir(
        host_category_id=1,
        directory_id=4,
        path="pub/fedora/linux/releases/26",
        up2date=True,
    )
    db.add(item)
    item = model.HostCategoryDir(
        host_category_id=3,
        directory_id=5,
        path="pub/fedora/linux/releases/27",
        up2date=True,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hostcategorydir_one_more(db):
    item = model.HostCategoryDir(
        host_category_id=3,
        directory_id=8,
        path="pub/fedora/linux/updates/testing/26/x86_64",
        up2date=True,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def hostcategorydir_even_more(db):
    item = model.HostCategoryDir(
        host_category_id=3,
        directory_id=9,
        path="pub/fedora/linux/updates/testing/27/x86_64",
        up2date=True,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def directoryexclusivehost(db):
    """Create some DirectoryExclusiveHost to play with for the tests"""
    item = model.DirectoryExclusiveHost(
        host_id=1,
        directory_id=4,
    )
    db.add(item)
    item = model.DirectoryExclusiveHost(
        host_id=3,
        directory_id=5,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def filedetail(db):
    """Create some FileDetail to play with for the tests"""
    item = model.FileDetail(
        filename="repomd.xml",
        directory_id=4,
        timestamp=1351758825,
        size=2972,
        sha1="foo_sha1",
        md5="foo_md5",
        sha256="foo_sha256",
        sha512="foo_sha512",
    )
    db.add(item)
    item = model.FileDetail(
        filename="repomd.xml",
        directory_id=7,
        timestamp=1357758825,
        size=2971,
        sha1="foo_sha1",
        md5="foo_md5",
        sha256="foo_sha256",
        sha512="foo_sha512",
    )
    db.add(item)
    item = model.FileDetail(
        filename="repomd.xml",
        directory_id=8,
        timestamp=1357758826,
        size=2972,
        sha1="foo2_sha1",
        md5="foo2_md5",
        sha256="foo2_sha256",
        sha512="foo2_sha512",
    )
    db.add(item)
    item = model.FileDetail(
        filename="repomd.xml",
        directory_id=9,
        timestamp=1357758827,
        size=2973,
        sha1="foo3_sha1",
        md5="foo3_md5",
        sha256="foo3_sha256",
        sha512="foo3_sha512",
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def user_groups(db):
    """Create some Grouip and UserGroup to play with for the tests"""
    item = model.Group(
        group_name="fpca",
        display_name="Fedora Project Contributor Agreement",
    )
    db.add(item)
    item = model.Group(
        group_name="packager",
        display_name="Fedora Packagers",
    )
    db.add(item)

    db.commit()

    item = model.UserGroup(
        user_id=1,
        group_id=1,
    )
    db.add(item)
    item = model.UserGroup(
        user_id=2,
        group_id=1,
    )
    db.add(item)
    item = model.UserGroup(
        user_id=3,
        group_id=1,
    )
    db.add(item)
    item = model.UserGroup(
        user_id=4,
        group_id=1,
    )
    db.add(item)

    item = model.UserGroup(
        user_id=1,
        group_id=2,
    )
    db.add(item)
    item = model.UserGroup(
        user_id=2,
        group_id=2,
    )
    db.add(item)
    item = model.UserGroup(
        user_id=4,
        group_id=2,
    )
    db.add(item)

    db.commit()


@pytest.fixture()
def db_items(
    base_items,
    site,
    site_admin,
    hosts,
    location,
    netblockcountry,
    directory,
    category,
    hostcategory,
    hostcategoryurl,
    hostcategorydir,
    hostcountry,
    hostpeerasn,
    hostnetblock,
    categorydirectory,
    version,
    repository,
    repositoryredirect,
):
    yield
