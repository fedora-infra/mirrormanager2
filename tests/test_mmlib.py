"""
mirrormanager2 tests.
"""

import mirrormanager2.lib


def test_query_directories(
    db,
    base_items,
    site,
    hosts,
    directory,
    category,
    hostcategory,
    hostcategoryurl,
    categorydirectory,
):
    """Test the query_directories function of mirrormanager2.lib."""
    results = mirrormanager2.lib.query_directories(db)
    assert len(results) == 12


def test_get_site(db, site):
    """Test the get_site function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_site(db, 0)
    assert results is None

    results = mirrormanager2.lib.get_site(db, 1)
    assert results.name == "test-mirror"
    assert results.private is False
    assert results.created_by == "pingou"

    results = mirrormanager2.lib.get_site(db, 2)
    assert results.name == "test-mirror2"
    assert results.private is False
    assert results.created_by == "kevin"

    results = mirrormanager2.lib.get_site(db, 3)
    assert results.name == "test-mirror_private"
    assert results.private is True
    assert results.created_by == "skvidal"


def test_get_site_by_name(db, site):
    """Test the get_site_by_name function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_site_by_name(db, "foo")
    assert results is None

    results = mirrormanager2.lib.get_site_by_name(db, "test-mirror")
    assert results.name == "test-mirror"
    assert results.private is False
    assert results.created_by == "pingou"

    results = mirrormanager2.lib.get_site_by_name(db, "test-mirror2")
    assert results.name == "test-mirror2"
    assert results.private is False
    assert results.created_by == "kevin"


def test_get_all_sites_empty(db):
    results = mirrormanager2.lib.get_all_sites(db)
    assert results == []


def test_get_all_sites(db, site):
    """Test the get_all_sites function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_all_sites(db)
    assert len(results) == 3
    assert results[0].name == "test-mirror"
    assert results[1].name == "test-mirror2"
    assert results[2].name == "test-mirror_private"


def test_get_siteadmin_no_site(db):
    """Test the get_siteadmin function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_siteadmin(db, 1)
    assert results is None


def test_get_siteadmin_no_siteadmin(db, site):
    """Test the get_siteadmin function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_siteadmin(db, 1)
    assert results is None


def test_get_siteadmin(db, site, site_admin):
    """Test the get_siteadmin function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_siteadmin(db, 1)
    assert results.site.name == "test-mirror"
    assert results.username == "ralph"

    results = mirrormanager2.lib.get_siteadmin(db, 4)
    assert results.site.name == "test-mirror2"
    assert results.username == "pingou"


def test_get_host_empty(db):
    results = mirrormanager2.lib.get_host(db, 1)
    assert results is None


def test_get_host(db, site, hosts):
    """Test the get_host function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_host(db, 1)
    assert results.name == "mirror.localhost"
    assert results.country == "US"

    results = mirrormanager2.lib.get_host(db, 2)
    assert results.name == "mirror2.localhost"
    assert results.country == "FR"

    results = mirrormanager2.lib.get_host(db, 3)
    assert results.name == "private.localhost"
    assert results.country == "NL"


def test_get_hosts_empty(db):
    results = mirrormanager2.lib.get_hosts(db)
    assert results == []


def test_get_hosts(db, site, hosts):
    """Test the get_hosts function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_hosts(db)
    assert len(results) == 4
    assert results[0].name == "mirror.localhost"
    assert results[0].country == "US"
    assert results[1].name == "mirror2.localhost"
    assert results[1].country == "FR"
    assert results[2].name == "private.localhost"
    assert results[2].country == "NL"


def test_get_host_acl_ip_empty(db):
    results = mirrormanager2.lib.get_host_acl_ip(db, 1)
    assert results is None


def test_get_host_acl_ip(db, site, hosts, hostaclip):
    """Test the get_host_acl_ip function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_host_acl_ip(db, 1)
    assert results.host.name == "mirror.localhost"
    assert results.host.country == "US"
    results = mirrormanager2.lib.get_host_acl_ip(db, 2)
    assert results.host.name == "mirror2.localhost"
    assert results.host.country == "FR"


def test_get_host_netblock_empty(db):
    results = mirrormanager2.lib.get_host_netblock(db, 1)
    assert results is None


def test_get_host_netblock(db, site, hosts, hostnetblock):
    """Test the get_host_netblock function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_host_netblock(db, 1)
    assert results.host.name == "private.localhost"
    assert results.host.country == "NL"
    results = mirrormanager2.lib.get_host_netblock(db, 2)
    assert results is None


def test_get_host_peer_asn_empty(db):
    results = mirrormanager2.lib.get_host_peer_asn(db, 1)
    assert results is None


def test_get_host_peer_asn(db, site, hosts, hostpeerasn):
    """Test the get_host_peer_asn function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_host_peer_asn(db, 1)
    assert results.host.name == "private.localhost"
    assert results.host.country == "NL"
    results = mirrormanager2.lib.get_host_peer_asn(db, 2)
    assert results is None


def test_get_host_country_empty(db):
    results = mirrormanager2.lib.get_host_country(db, 1)
    assert results is None


def test_get_host_country(db, base_items, site, hosts, hostcountry):
    """Test the get_host_country function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_host_country(db, 1)
    assert results.host.name == "mirror.localhost"
    assert results.host.country == "US"
    results = mirrormanager2.lib.get_host_country(db, 2)
    assert results.host.name == "mirror2.localhost"
    assert results.host.country == "FR"
    results = mirrormanager2.lib.get_host_country(db, 3)
    assert results is None


def test_get_host_category_empty(db):
    results = mirrormanager2.lib.get_host_category(db, 1)
    assert results is None


def test_get_host_category(db, base_items, site, hosts, directory, category, hostcategory):
    """Test the get_host_category function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_host_category(db, 1)
    assert results.host.name == "mirror.localhost"
    assert results.host.country == "US"
    results = mirrormanager2.lib.get_host_category(db, 2)
    assert results.host.name == "mirror.localhost"
    assert results.host.country == "US"
    results = mirrormanager2.lib.get_host_category(db, 3)
    assert results.host.name == "mirror2.localhost"
    assert results.host.country == "FR"
    results = mirrormanager2.lib.get_host_category(db, 4)
    assert results.host.name == "mirror2.localhost"
    assert results.host.country == "FR"
    results = mirrormanager2.lib.get_host_category(db, 5)
    assert results is None


def test_get_host_category_by_hostid_category_empty(db):
    result = mirrormanager2.lib.get_host_category_by_hostid_category(db, 1, "Fedora Linux")
    assert result is None


def test_get_host_category_by_hostid_category(
    db, base_items, site, hosts, directory, category, hostcategory
):
    """Test the get_host_category_by_hostid_category function of
    mirrormanager2.lib.
    """
    result = mirrormanager2.lib.get_host_category_by_hostid_category(db, 1, "Fedora Linux")
    assert result is not None
    assert result.host.name == "mirror.localhost"
    assert result.host.country == "US"

    result = mirrormanager2.lib.get_host_category_by_hostid_category(db, 2, "Fedora Linux")
    assert result is not None
    assert result.host.name == "mirror2.localhost"
    assert result.host.country == "FR"

    result = mirrormanager2.lib.get_host_category_by_hostid_category(db, 3, "Fedora Linux")
    assert result is None


def test_get_host_category_url_by_id_empty(db):
    results = mirrormanager2.lib.get_host_category_url_by_id(db, 1)
    assert results is None


def test_get_host_category_url_by_id(
    db, base_items, site, hosts, directory, category, hostcategory, hostcategoryurl
):
    """Test the get_host_category_url_by_id function of
    mirrormanager2.lib.
    """
    for i in range(4):
        results = mirrormanager2.lib.get_host_category_url_by_id(db, i + 1)
        assert results.host_category.host.name == "mirror.localhost"
        assert results.host_category.host.country == "US"

    results = mirrormanager2.lib.get_host_category_url_by_id(db, 9)
    assert results is None


def test_get_host_category_url_empty(db):
    results = mirrormanager2.lib.get_host_category_url(db)
    assert results == []


def test_get_host_category_url(
    db, base_items, site, hosts, directory, category, hostcategory, hostcategoryurl
):
    """Test the get_host_category_url function of
    mirrormanager2.lib.
    """
    results = mirrormanager2.lib.get_host_category_url(db)
    assert len(results) == 8
    for i in range(4):
        assert results[i].host_category.host.name == "mirror.localhost"
        assert results[i].host_category.host.country == "US"


def test_get_country_by_name_empty(db):
    results = mirrormanager2.lib.get_country_by_name(db, "FR")
    assert results is None


def test_get_country_by_name(db, base_items):
    """Test the get_country_by_name function of
    mirrormanager2.lib.
    """
    for i in ["FR", "US"]:
        results = mirrormanager2.lib.get_country_by_name(db, i)
        assert results.code == i

    results = mirrormanager2.lib.get_country_by_name(db, "BE")
    assert results is None


def test_get_country_continent_redirect_empty(db):
    results = mirrormanager2.lib.get_country_continent_redirect(db)
    assert results == []


def test_get_country_continent_redirect(db, base_items):
    """Test the get_country_continent_redirect function of
    mirrormanager2.lib.
    """
    results = mirrormanager2.lib.get_country_continent_redirect(db)
    assert len(results) == 3
    assert results[0].country == "IL"
    assert results[0].continent == "EU"
    assert results[1].country == "AM"
    assert results[1].continent == "EU"
    assert results[2].country == "JO"
    assert results[2].continent == "EU"


def test_get_user_by_username_empty(db):
    """Test the get_user_by_username function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_user_by_username(db, "pingou")
    assert results is None


def test_get_user_by_username(db, base_items):
    """Test the get_user_by_username function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_user_by_username(db, "pingou")
    assert results.user_name == "pingou"
    assert results.email_address == "pingou@fp.o"

    results = mirrormanager2.lib.get_user_by_username(db, "ralph")
    assert results.user_name == "ralph"
    assert results.email_address == "ralph@fp.o"

    results = mirrormanager2.lib.get_user_by_username(db, "foo")
    assert results is None


def test_get_user_by_email_empty(db):
    results = mirrormanager2.lib.get_user_by_email(db, "pingou@fp.o")
    assert results is None


def test_get_user_by_email(db, base_items):
    """Test the get_user_by_email function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_user_by_email(db, "pingou@fp.o")
    assert results.user_name == "pingou"
    assert results.email_address == "pingou@fp.o"

    results = mirrormanager2.lib.get_user_by_email(db, "ralph@fp.o")
    assert results.user_name == "ralph"
    assert results.email_address == "ralph@fp.o"

    results = mirrormanager2.lib.get_user_by_email(db, "foo")
    assert results is None


def test_get_user_by_token_empty(db):
    results = mirrormanager2.lib.get_user_by_token(db, "bar")
    assert results is None


def test_get_user_by_token(db, base_items):
    """Test the get_user_by_token function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_user_by_token(db, "bar")
    assert results.user_name == "shaiton"
    assert results.email_address == "shaiton@fp.o"

    results = mirrormanager2.lib.get_user_by_token(db, "foo")
    assert results is None


def test_get_session_by_visitkey_empty(db):
    results = mirrormanager2.lib.get_session_by_visitkey(db, "foo")
    assert results is None


def test_get_session_by_visitkey(db, base_items):
    """Test the get_session_by_visitkey function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_session_by_visitkey(db, "foo")
    assert results.user.user_name == "pingou"
    assert results.user.email_address == "pingou@fp.o"
    assert results.user_ip == "127.0.0.1"

    results = mirrormanager2.lib.get_session_by_visitkey(db, "bar")
    assert results is None


def test_get_version_by_name_version_empty(db):
    results = mirrormanager2.lib.get_version_by_name_version(db, "Fedora", "21")
    assert results is None


def test_get_version_by_name_version(db, base_items, version):
    """Test the get_version_by_name_version function of
    mirrormanager2.lib.
    """
    results = mirrormanager2.lib.get_version_by_name_version(db, "Fedora", 27)
    assert results.product.name == "Fedora"
    assert results.name == "27"

    results = mirrormanager2.lib.get_version_by_name_version(db, "Fedora", "27-alpha")
    assert results.product.name == "Fedora"
    assert results.name == "27-alpha"
    assert results.is_test is True

    results = mirrormanager2.lib.get_session_by_visitkey(db, "bar")
    assert results is None


def test_get_versions_empty(db):
    results = mirrormanager2.lib.get_versions(db)
    assert results == []


def test_get_versions(db, base_items, version):
    """Test the get_versions function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_versions(db)
    assert len(results) == 6
    assert results[0].product.name == "Fedora"
    assert results[0].name == "26"
    assert results[1].product.name == "Fedora"
    assert results[1].name == "27-alpha"
    assert results[2].product.name == "Fedora"
    assert results[2].name == "27"


def test_get_arch_by_name_empty(db):
    results = mirrormanager2.lib.get_arch_by_name(db, "i386")
    assert results is None


def test_get_arch_by_name(db, base_items):
    """Test the get_arch_by_name function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_arch_by_name(db, "i386")
    assert results.name == "i386"

    results = mirrormanager2.lib.get_arch_by_name(db, "i686")
    assert results is None


def test_get_categories_empty(db):
    results = mirrormanager2.lib.get_categories(db)
    assert results == []


def test_get_categories(db, base_items, directory, category):
    """Test the get_categories function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_categories(db)
    assert len(results) == 3
    assert results[0].name == "Fedora Linux"
    assert results[0].product.name == "Fedora"
    assert results[1].name == "Fedora EPEL"
    assert results[1].product.name == "EPEL"
    assert results[2].name == "Fedora Codecs"
    assert results[2].product.name == "Fedora"

    results = mirrormanager2.lib.get_categories(db, True)
    assert len(results) == 2
    assert results[0].name == "Fedora Linux"
    assert results[0].product.name == "Fedora"
    assert results[1].name == "Fedora EPEL"
    assert results[1].product.name == "EPEL"


def test_get_category_by_name_empty(db):
    results = mirrormanager2.lib.get_category_by_name(db, "Fedora EPEL")
    assert results is None


def test_get_category_by_name(db, base_items, directory, category):
    """Test the get_category_by_name function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_category_by_name(db, "Fedora EPEL")
    assert results.name == "Fedora EPEL"
    assert results.product.name == "EPEL"

    results = mirrormanager2.lib.get_category_by_name(db, "Fedora Linux")
    assert results.name == "Fedora Linux"
    assert results.product.name == "Fedora"

    results = mirrormanager2.lib.get_category_by_name(db, "foo")
    assert results is None


def test_get_category_directory_empty(db):
    results = mirrormanager2.lib.get_category_directory(db)
    assert results == []


def test_get_category_directory(db, base_items, directory, category, categorydirectory):
    """Test the get_category_directory function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_category_directory(db)
    assert len(results) == 4
    assert results[0].category.name == "Fedora Linux"
    assert results[0].directory.name == "pub/fedora/linux"
    assert results[1].category.name == "Fedora EPEL"
    assert results[1].directory.name == "pub/epel"


def test_get_product_by_name_empty(db):
    results = mirrormanager2.lib.get_product_by_name(db, "Fedora")
    assert results is None


def test_get_product_by_name(db, base_items):
    """Test the get_product_by_name function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_product_by_name(db, "Fedora")
    assert results.name == "Fedora"

    results = mirrormanager2.lib.get_product_by_name(db, "EPEL")
    assert results.name == "EPEL"

    results = mirrormanager2.lib.get_product_by_name(db, "foo")
    assert results is None


def test_get_products_empty(db):
    results = mirrormanager2.lib.get_products(db)
    assert results == []


def test_get_products(db, base_items):
    """Test the get_products function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_products(db)
    assert len(results) == 2
    assert results[0].name == "EPEL"
    assert results[1].name == "Fedora"


def test_get_repo_prefix_arch_empty(db):
    results = mirrormanager2.lib.get_repo_prefix_arch(db, "updates-testing-f20", "x86_64")
    assert results is None


def test_get_repo_prefix_arch(db, base_items, version, directory, category, repository):
    """Test the get_repo_prefix_arch function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_repo_prefix_arch(db, "updates-testing-f26", "x86_64")
    assert results.name == "pub/fedora/linux/updates/testing/26/x86_64"

    results = mirrormanager2.lib.get_repo_prefix_arch(db, "updates-testing-f27", "x86_64")
    assert results.name == "pub/fedora/linux/updates/testing/27/x86_64"

    results = mirrormanager2.lib.get_repo_prefix_arch(db, "updates-testing-f20", "i386")
    assert results is None


def test_get_repo_by_name_empty(db):
    results = mirrormanager2.lib.get_repo_by_name(db, "pub/fedora/linux/updates/testing/19/x86_64")
    assert results is None


def test_get_repo_by_name(db, base_items, version, directory, category, repository):
    """Test the get_repo_by_name function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_repo_by_name(db, "pub/fedora/linux/updates/testing/25/x86_64")
    assert results.name == "pub/fedora/linux/updates/testing/25/x86_64"

    results = mirrormanager2.lib.get_repo_by_name(db, "pub/fedora/linux/updates/testing/26/x86_64")
    assert results.name == "pub/fedora/linux/updates/testing/26/x86_64"

    results = mirrormanager2.lib.get_repo_by_name(db, "pub/fedora/linux/updates/testing/19/i386")
    assert results is None


def test_get_repo_by_dir_empty(db):
    results = mirrormanager2.lib.get_repo_by_dir(db, "pub/fedora/linux/updates/testing/21/x86_64")
    assert results == []


def test_get_repo_by_dir(db, base_items, version, directory, category, repository):
    """Test the get_repo_by_dir function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_repo_by_dir(db, "pub/fedora/linux/updates/testing/27/x86_64")
    assert len(results) == 1
    assert results[0].name == "pub/fedora/linux/updates/testing/27/x86_64"
    assert results[0].arch.name == "x86_64"


def test_get_repositories_empty(db):
    results = mirrormanager2.lib.get_repositories(db)
    assert results == []


def test_get_repositories(db, base_items, version, directory, category, repository):
    """Test the get_repositories function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_repositories(db)
    assert len(results) == 4
    assert results[0].name == "pub/fedora/linux/updates/testing/25/x86_64"
    assert results[0].arch.name == "x86_64"

    assert results[1].name == "pub/fedora/linux/updates/testing/26/x86_64"
    assert results[1].arch.name == "x86_64"

    assert results[2].name == "pub/fedora/linux/updates/testing/27/x86_64"
    assert results[2].arch.name == "x86_64"


def test_get_reporedirect_empty(db):
    results = mirrormanager2.lib.get_reporedirect(db)
    assert results == []


def test_get_reporedirect(db, repositoryredirect):
    """Test the get_reporedirect function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_reporedirect(db)
    assert len(results) == 3
    assert results[0].from_repo == "fedora-rawhide"
    assert results[0].to_repo == "rawhide"
    assert results[1].from_repo == "fedora-install-rawhide"
    assert results[1].to_repo == "rawhide"
    assert results[2].from_repo == "epel-6.0"
    assert results[2].to_repo == "epel-6"


def test_get_arches_empty(db):
    results = mirrormanager2.lib.get_arches(db)
    assert results == []


def test_get_arches(db, base_items):
    """Test the get_arches function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_arches(db)
    assert len(results) == 4
    assert results[0].name == "i386"
    assert results[1].name == "ppc"
    assert results[2].name == "source"
    assert results[3].name == "x86_64"


def test_add_admin_to_site(db, base_items, site):
    """Test the add_admin_to_site function of mirrormanager2.lib."""
    site = mirrormanager2.lib.get_site(db, 1)

    results = mirrormanager2.lib.add_admin_to_site(db, site, "pingou")
    assert results == "pingou added as an admin"

    results = mirrormanager2.lib.add_admin_to_site(db, site, "pingou")
    assert results == "pingou was already listed as an admin"


def test_get_locations_empty(db):
    results = mirrormanager2.lib.get_locations(db)
    assert results == []


def test_get_locations(db, location):
    """Test the get_locations function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_locations(db)
    assert len(results) == 3
    assert results[0].name == "foo"
    assert results[1].name == "bar"
    assert results[2].name == "foobar"


def test_get_netblock_country_empty(db):
    results = mirrormanager2.lib.get_netblock_country(db)
    assert results == []


def test_get_netblock_country(db, netblockcountry):
    """Test the get_netblock_country function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_netblock_country(db)
    assert len(results) == 1
    assert results[0].netblock == "127.0.0.0/24"
    assert results[0].country == "AU"


def check_results_host(results):
    for result in results:
        if result.id == 1:
            assert result.name == "mirror.localhost"
        elif result.id == 2:
            assert result.name == "mirror2.localhost"
        elif result.id == 3:
            assert result.name == "private.localhost"
        elif result.id == 4:
            assert result.name == "Another test entry"
        else:
            raise AssertionError


def test_get_mirrors_empty(db):
    results = mirrormanager2.lib.get_mirrors(db)
    assert results == []


def test_get_mirrors(
    db,
    base_items,
    site,
    hosts,
    directory,
    category,
    hostcategory,
    hostcategoryurl,
    categorydirectory,
    netblockcountry,
    version,
    repository,
):
    """Test the get_mirrors function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_mirrors(db)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, private=True)
    assert len(results) == 1
    assert results[0].name == "private.localhost"

    results = mirrormanager2.lib.get_mirrors(db, internet2=True)
    assert len(results) == 0

    results = mirrormanager2.lib.get_mirrors(db, internet2_clients=True)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, internet2_clients=False)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, asn_clients=True)
    assert len(results) == 1
    assert results[0].name == "mirror2.localhost"
    results = mirrormanager2.lib.get_mirrors(db, asn_clients=False)
    assert len(results) == 3
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, admin_active=False)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, admin_active=True)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, user_active=False)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, user_active=True)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, host_category_url_private=True)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, host_category_url_private=False)
    assert len(results) == 2
    assert results[0].name == "mirror2.localhost"

    results = mirrormanager2.lib.get_mirrors(db, last_crawl_duration=True)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, last_crawl_duration=False)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, last_crawled=True)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, last_crawled=False)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, last_checked_in=True)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, last_checked_in=False)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, site_private=True)
    assert len(results) == 1
    results = mirrormanager2.lib.get_mirrors(db, site_private=False)
    assert len(results) == 3
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, site_user_active=False)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, site_user_active=True)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, site_admin_active=False)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, site_admin_active=True)
    assert len(results) == 4
    check_results_host(results)

    results = mirrormanager2.lib.get_mirrors(db, up2date=True)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, up2date=False)
    assert len(results) == 0

    results = mirrormanager2.lib.get_mirrors(db, arch_id=1)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, arch_id=3)
    assert len(results) == 2
    check_results_host(results)


def test_get_mirrors_version_empty(
    db,
    base_items,
    site,
    hosts,
    directory,
    category,
    hostcategory,
    hostcategoryurl,
    categorydirectory,
    netblockcountry,
):
    results = mirrormanager2.lib.get_mirrors(db, version_id=1)
    assert len(results) == 0
    results = mirrormanager2.lib.get_mirrors(db, version_id=4)


def test_get_mirrors_version(
    db,
    base_items,
    site,
    hosts,
    directory,
    category,
    hostcategory,
    hostcategoryurl,
    categorydirectory,
    netblockcountry,
    version,
    repository,
):
    results = mirrormanager2.lib.get_mirrors(db, version_id=1)
    assert len(results) == 2
    assert results[0].name == "mirror2.localhost"
    assert results[1].name == "mirror.localhost"
    results = mirrormanager2.lib.get_mirrors(db, version_id=3)
    assert len(results) == 2
    check_results_host(results)


def test_get_user_sites_empty(db):
    results = mirrormanager2.lib.get_user_sites(db, "pingou")
    assert results == []


def test_get_user_sites(db, base_items, site):
    """Test the get_user_sites function of mirrormanager2.lib."""
    site = mirrormanager2.lib.get_site(db, 1)
    mirrormanager2.lib.add_admin_to_site(db, site, "pingou")
    results = mirrormanager2.lib.get_user_sites(db, "pingou")
    assert len(results) == 1
    assert results[0].name == "test-mirror"


def test_id_generator():
    """Test the id_generator function of mirrormanager2.lib."""
    results = mirrormanager2.lib.id_generator(size=5, chars=["a"])
    assert results == "aaaaa"

    results = mirrormanager2.lib.id_generator(size=5, chars=["1"])
    assert results == "11111"


def test_get_directory_by_name_empty(db):
    results = mirrormanager2.lib.get_directory_by_name(db, "pub/epel")
    assert results is None


def test_get_directory_by_name(db, directory):
    """Test the get_directory_by_name function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_directory_by_name(db, "pub/epel")
    assert results.name == "pub/epel"
    assert results.readable is True

    results = mirrormanager2.lib.get_directory_by_name(db, "pub/fedora/linux/extras")
    assert results.name == "pub/fedora/linux/extras"
    assert results.readable is True

    results = mirrormanager2.lib.get_directory_by_name(
        db, "pub/fedora/linux/updates/testing/25/x86_64"
    )
    assert results.name == "pub/fedora/linux/updates/testing/25/x86_64"
    assert results.readable is True


def test_get_directories_empty(db):
    results = mirrormanager2.lib.get_directories(db)
    assert results == []


def test_get_directories(db, directory):
    """Test the get_directories function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_directories(db)
    assert len(results) == 9
    assert results[0].name == "pub/fedora/linux"
    assert results[1].name == "pub/fedora/linux/extras"
    assert results[2].name == "pub/epel"


def test_get_directory_by_id_empty(db):
    results = mirrormanager2.lib.get_directory_by_id(db, 1)
    assert results is None


def test_get_directory_by_id(db, directory):
    """Test the get_directory_by_id function of mirrormanager2.lib."""
    results = mirrormanager2.lib.get_directory_by_id(db, 3)
    assert results.name == "pub/epel"
    assert results.readable is True

    results = mirrormanager2.lib.get_directory_by_id(db, 2)
    assert results.name == "pub/fedora/linux/extras"
    assert results.readable is True

    results = mirrormanager2.lib.get_directory_by_id(db, 4)
    assert results.name == "pub/fedora/linux/releases/26"
    assert results.readable is True


def test_get_hostcategorydir_by_hostcategoryid_and_path_empty(db):
    results = mirrormanager2.lib.get_hostcategorydir_by_hostcategoryid_and_path(
        db, 2, "pub/fedora/linux/releases/21"
    )
    assert results == []


def test_get_hostcategorydir_by_hostcategoryid_and_path(
    db, base_items, site, hosts, directory, category, hostcategory, hostcategorydir
):
    """Test the get_hostcategorydir_by_hostcategoryid_and_path
    function of mirrormanager2.lib.
    """
    results = mirrormanager2.lib.get_hostcategorydir_by_hostcategoryid_and_path(
        db, 3, "pub/fedora/linux/releases/27"
    )
    assert len(results) == 1
    assert results[0].directory.name == "pub/fedora/linux/releases/27"
    assert results[0].host_category.category.name == "Fedora Linux"


def test_get_directory_exclusive_host_empty(db):
    results = mirrormanager2.lib.get_directory_exclusive_host(db)
    assert results == []


def test_get_directory_exclusive_host(
    db, base_items, site, hosts, directory, directoryexclusivehost
):
    """Test the get_directory_exclusive_host function of
    mirrormanager2.lib.
    """
    results = mirrormanager2.lib.get_directory_exclusive_host(db)
    assert len(results) == 2
    assert results[0].dname == "pub/fedora/linux/releases/26"
    assert results[0].host_id == 1
    assert results[1].dname == "pub/fedora/linux/releases/27"
    assert results[1].host_id == 3


def test_get_file_detail_empty(db):
    results = mirrormanager2.lib.get_file_detail(db, "repomd.xml", 7)
    assert results is None


def test_get_file_detail(db, directory, filedetail):
    """Test the get_file_detail function of
    mirrormanager2.lib.
    """
    results = mirrormanager2.lib.get_file_detail(db, "repomd.xml", 7)
    assert results.md5 == "foo_md5"
    assert results.directory.name == "pub/fedora/linux/updates/testing/25/x86_64"

    results = mirrormanager2.lib.get_file_detail(db, "repomd.xml", 7, md5="foo_md5")
    assert results.md5 == "foo_md5"
    assert results.directory.name == "pub/fedora/linux/updates/testing/25/x86_64"

    results = mirrormanager2.lib.get_file_detail(db, "repomd.xml", 7, sha1="foo_sha1")
    assert results.md5 == "foo_md5"
    assert results.directory.name == "pub/fedora/linux/updates/testing/25/x86_64"

    results = mirrormanager2.lib.get_file_detail(db, "repomd.xml", 7, sha256="foo_sha256")
    assert results.md5 == "foo_md5"
    assert results.directory.name == "pub/fedora/linux/updates/testing/25/x86_64"

    results = mirrormanager2.lib.get_file_detail(db, "repomd.xml", 7, sha512="foo_sha512")
    assert results.md5 == "foo_md5"
    assert results.directory.name == "pub/fedora/linux/updates/testing/25/x86_64"

    results = mirrormanager2.lib.get_file_detail(db, "repomd.xml", 7, size=2973)
    assert results is None

    results = mirrormanager2.lib.get_file_detail(db, "repomd.xml", 7, timestamp=1357758825)
    assert results.md5 == "foo_md5"
    assert results.directory.name == "pub/fedora/linux/updates/testing/25/x86_64"
