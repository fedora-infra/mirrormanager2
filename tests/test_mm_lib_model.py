"""
mirrormanager2 model tests.
"""

import mirrormanager2.lib
import mirrormanager2.lib.model as model


def test_mirrormanagerbasemixin(db, base_items):
    """Test the MirrorManagerBaseMixin object of
    mirrormanager2.lib.model.
    """
    item = model.Arch.get_by_pk(1)
    assert item.name == "source"
    item = model.Arch.get_by_pk(3)
    assert item.name == "x86_64"


def test_site_repr(db, site):
    """Test the Site.__repr__ object of mirrormanager2.lib.model."""
    item = model.Site.get_by_pk(1)
    assert str(item) == "<Site(1 - test-mirror)>"
    item = model.Site.get_by_pk(3)
    assert str(item) == "<Site(3 - test-mirror_private)>"


def test_host_repr(db, site, hosts):
    """Test the Host.__repr__ object of mirrormanager2.lib.model."""
    item = model.Host.get_by_pk(1)
    assert str(item) == "<Host(1 - mirror.localhost)>"
    item = model.Host.get_by_pk(3)
    assert str(item) == "<Host(3 - private.localhost)>"


def test_host_json(db, site, hosts):
    """Test the Host.__json__ object of mirrormanager2.lib.model."""
    item = model.Host.get_by_pk(1)
    assert item.__json__() == {
        "admin_active": True,
        "asn": None,
        "asn_clients": False,
        "bandwidth_int": 100,
        "comment": None,
        "country": "US",
        "id": 1,
        "internet2": False,
        "internet2_clients": False,
        "last_checked_in": None,
        "last_crawl_duration": 0,
        "last_crawled": None,
        "max_connections": 10,
        "name": "mirror.localhost",
        "private": False,
        "site": {"id": 1, "name": "test-mirror"},
        "user_active": True,
    }
    item = model.Host.get_by_pk(3)
    assert item.__json__() == {
        "admin_active": True,
        "asn": None,
        "asn_clients": False,
        "bandwidth_int": 100,
        "comment": "My own private mirror",
        "country": "NL",
        "id": 3,
        "internet2": False,
        "internet2_clients": False,
        "last_checked_in": None,
        "last_crawl_duration": 0,
        "last_crawled": None,
        "max_connections": 10,
        "name": "private.localhost",
        "private": True,
        "site": {"id": 1, "name": "test-mirror"},
        "user_active": True,
    }


def test_host_set_not_up2date(
    db, site, hosts, base_items, directory, category, hostcategory, hostcategorydir
):
    """Test the Host.set_not_up2date object of mirrormanager2.lib.model."""
    item = model.Host.get_by_pk(1)
    # Before change, all is up2date
    for hc in item.categories:
        for hcd in hc.directories:
            assert hcd.up2date

    item.set_not_up2date(db)

    # After change, all is *not* up2date
    for hc in item.categories:
        for hcd in hc.directories:
            assert not hcd.up2date


def test_host_is_active(db, site, hosts):
    """Test the Host.is_active object of mirrormanager2.lib.model."""
    item = model.Host.get_by_pk(1)
    assert item.is_active()

    item.admin_active = False
    db.add(item)
    db.commit()

    item = model.Host.get_by_pk(1)
    assert not item.is_active()


def test_directory_repr(db, base_items, directory):
    """Test the Directory.__repr__ object of mirrormanager2.lib.model."""
    item = model.Directory.get_by_pk(1)
    assert str(item) == "<Directory(1 - pub/fedora/linux)>"
    item = model.Directory.get_by_pk(3)
    assert str(item) == "<Directory(3 - pub/epel)>"


def test_product_repr(db, base_items):
    """Test the Product.__repr__ object of mirrormanager2.lib.model."""
    item = model.Product.get_by_pk(1)
    assert str(item) == "<Product(1 - EPEL)>"
    item = model.Product.get_by_pk(2)
    assert str(item) == "<Product(2 - Fedora)>"


def test_product_displayed_versions_empty(db, base_items):
    """Test the Product.displayed_versions object of mirrormanager2.lib.model."""
    item = model.Product.get_by_pk(1)
    assert item.displayed_versions == []


def test_product_displayed_versions(db, base_items, version):
    """Test the Product.displayed_versions object of mirrormanager2.lib.model."""
    item = model.Product.get_by_pk(1)
    assert item.displayed_versions[0].name == "7"

    item = model.Product.get_by_pk(2)
    for index, string in enumerate(["development", "27", "26", "25"]):
        assert item.displayed_versions[index].name == string


def test_category_repr(db, base_items, directory, category):
    """Test the Category.__repr__ object of mirrormanager2.lib.model."""
    item = model.Category.get_by_pk(1)
    assert str(item) == "<Category(1 - Fedora Linux)>"
    item = model.Category.get_by_pk(2)
    assert str(item) == "<Category(2 - Fedora EPEL)>"


def test_hostcategory_repr(db, base_items, directory, category, site, hosts, hostcategory):
    """Test the HostCategory.__repr__ object of mirrormanager2.lib.model."""
    item = model.HostCategory.get_by_pk(1)
    assert str(item) == "<HostCategory(1 - <Category(1 - Fedora Linux)>)>"
    item = model.HostCategory.get_by_pk(2)
    assert str(item) == "<HostCategory(2 - <Category(2 - Fedora EPEL)>)>"


def test_categorydirectory_repr(db, base_items, directory, category, categorydirectory):
    """Test the CategoryDirectory.__repr__ object of mirrormanager2.lib.model."""
    item = mirrormanager2.lib.get_category_directory(db)
    assert str(item[0]) == "<CategoryDirectory(1 - 1)>"
    assert str(item[1]) == "<CategoryDirectory(2 - 3)>"


def test_arch_repr(db, base_items):
    """Test the Arch.__repr__ object of mirrormanager2.lib.model."""
    item = model.Arch.get_by_pk(1)
    assert str(item) == "<Arch(1 - source)>"
    item = model.Arch.get_by_pk(2)
    assert str(item) == "<Arch(2 - i386)>"


def test_version_repr(db, base_items, version):
    """Test the Version.__repr__ object of mirrormanager2.lib.model."""
    item = model.Version.get_by_pk(1)
    assert str(item) == "<Version(1 - 26)>"
    item = model.Version.get_by_pk(2)
    assert str(item) == "<Version(2 - 27-alpha)>"


def test_version_arches(db, base_items, version, directory, category, repository):
    """Test the Version.arches object of mirrormanager2.lib.model."""
    item = model.Version.get_by_pk(1)
    assert item.arches == set(["x86_64"])
    item = model.Version.get_by_pk(2)
    assert item.arches == set([])
    item = model.Version.get_by_pk(3)
    assert item.arches == set(["x86_64"])


def test_group_repr(db, base_items, user_groups):
    """Test the Group.__repr__ object of mirrormanager2.lib.model."""
    item = model.Group.get_by_pk(1)
    assert str(item) == "Group: 1 - name fpca"
    item = model.Group.get_by_pk(2)
    assert str(item) == "Group: 2 - name packager"


def test_user_repr(db, base_items, user_groups):
    """Test the User.__repr__ object of mirrormanager2.lib.model."""
    item = model.User.get_by_pk(1)
    assert str(item) == "User: 1 - name pingou"
    item = model.User.get_by_pk(2)
    assert str(item) == "User: 2 - name kevin"
    item = model.User.get_by_pk(4)
    assert str(item) == "User: 4 - name shaiton"


def test_user_username(db, base_items, user_groups):
    """Test the User.username object of mirrormanager2.lib.model."""
    for index, string in enumerate(["pingou", "kevin", "ralph", "shaiton"]):
        item = model.User.get_by_pk(index + 1)
        assert item.username == string


def test_user_groups(db, base_items, user_groups):
    """Test the User.groups object of mirrormanager2.lib.model."""
    item = model.User.get_by_pk(1)
    assert item.groups == ["fpca", "packager"]
    item = model.User.get_by_pk(2)
    assert item.groups == ["fpca", "packager"]
    item = model.User.get_by_pk(3)
    assert item.groups == ["fpca"]
    item = model.User.get_by_pk(4)
    assert item.groups == ["fpca", "packager"]
