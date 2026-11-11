"""
mirrormanager2 tests for the `Move To Archive` (MTA) script.
"""

import os

import pytest
import sqlalchemy as sa
from click.testing import CliRunner

import mirrormanager2.lib
import mirrormanager2.lib.model as model
from mirrormanager2.utility import move_to_archive

FOLDER = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def configfile(tmp_path, db_url):
    path = tmp_path.joinpath("mirrormanager2_tests.cfg").as_posix()
    contents = f"""
SQLALCHEMY_DATABASE_URI = {db_url!r}
import os
DB_ALEMBIC_LOCATION = os.path.join("{FOLDER}", "..", "mirrormanager2", "lib", "migrations")


# Specify whether the crawler should send a report by email
CRAWLER_SEND_EMAIL =  False

    """
    with open(path, "w") as stream:
        stream.write(contents)
    return path


@pytest.fixture()
def command_args(configfile):
    return ["-c", configfile, "--product", "Fedora", "--version", "26"]


def run_command(args):
    runner = CliRunner()
    return runner.invoke(move_to_archive.main, args)


def _make_archive_category(db):
    item = model.Directory(
        name="pub/archive",
        readable=True,
    )
    db.add(item)
    db.flush()
    item = model.Category(
        name="Fedora Archive",
        product_id=1,
        canonicalhost="http://archive.fedoraproject.org",
        topdir_id=item.id,
        publiclist=True,
    )
    db.add(item)
    db.commit()


@pytest.fixture()
def split_layout(db, base_items):
    """Two categories of one product whose archive trees replace their top directory,
    as on RPM Fusion: free/fedora is archived to free-archive/fedora."""
    product = mirrormanager2.lib.get_product_by_name(db, "Fedora")
    version = model.Version(name="42", product=product)
    arch = mirrormanager2.lib.get_arch_by_name(db, "x86_64")
    db.add(version)
    for repo in ("free", "nonfree"):
        for suffix in ("", "-archive"):
            topdir = model.Directory(name=f"{repo}{suffix}/fedora", readable=True)
            category = model.Category(
                name=f"RPMFUSION {repo} Fedora{' Archive' if suffix else ''}",
                product=product,
                topdir=topdir,
            )
            directory = model.Directory(
                name=f"{repo}{suffix}/fedora/updates/42/x86_64", readable=True
            )
            db.add_all([topdir, category, directory])
            if not suffix:
                db.add(
                    model.Repository(
                        name=directory.name,
                        prefix=f"{repo}-fedora-updates-released-42",
                        category=category,
                        version=version,
                        arch=arch,
                        directory=directory,
                    )
                )
    db.commit()


def _repo_directories(db):
    return {
        repo.prefix: (repo.category.name, repo.directory.name)
        for repo in mirrormanager2.lib.get_repositories(db)
    }


def test_mta_split_layout_without_category(configfile, db, split_layout):
    """Without --category, the archive directory keeps the live top directory."""
    result = run_command(
        [
            "-c",
            configfile,
            "--product",
            "Fedora",
            "--version",
            "42",
            "--archive-category",
            "RPMFUSION free Fedora Archive",
        ]
    )
    assert result.exit_code == 1, result.output
    assert result.output == (
        "Error: Unable to find a directory in [RPMFUSION free Fedora Archive] "
        "for free/fedora/updates/42/x86_64\n"
    )


def test_mta_category(configfile, db, split_layout):
    """--category replaces the top directory and leaves other categories alone."""
    result = run_command(
        [
            "-c",
            configfile,
            "--product",
            "Fedora",
            "--version",
            "42",
            "--category",
            "RPMFUSION free Fedora",
            "--archive-category",
            "RPMFUSION free Fedora Archive",
        ]
    )
    assert result.exit_code == 0, result.output
    assert result.output == (
        "free/fedora/updates/42/x86_64 => free-archive/fedora/updates/42/x86_64\n"
    )
    assert _repo_directories(db) == {
        "free-fedora-updates-released-42": (
            "RPMFUSION free Fedora Archive",
            "free-archive/fedora/updates/42/x86_64",
        ),
        "nonfree-fedora-updates-released-42": (
            "RPMFUSION nonfree Fedora",
            "nonfree/fedora/updates/42/x86_64",
        ),
    }


def test_mta_missing_directory_changes_nothing(configfile, db, split_layout):
    """A missing archive directory aborts the run before any repository is moved."""
    first = mirrormanager2.lib.get_repo_prefix_arch(db, "free-fedora-updates-released-42", "x86_64")
    directory = model.Directory(name="free/fedora/updates/testing/42/x86_64", readable=True)
    db.add(
        model.Repository(
            name=directory.name,
            prefix="free-fedora-updates-testing-42",
            category=first.category,
            version=first.version,
            arch=first.arch,
            directory=directory,
        )
    )
    db.commit()
    result = run_command(
        [
            "-c",
            configfile,
            "--product",
            "Fedora",
            "--version",
            "42",
            "--category",
            "RPMFUSION free Fedora",
            "--archive-category",
            "RPMFUSION free Fedora Archive",
        ]
    )
    assert result.exit_code == 1, result.output
    assert result.output == (
        "Error: Unable to find a directory in [RPMFUSION free Fedora Archive] "
        "for free/fedora/updates/testing/42/x86_64\n"
    )
    db.expire_all()
    assert _repo_directories(db)["free-fedora-updates-released-42"] == (
        "RPMFUSION free Fedora",
        "free/fedora/updates/42/x86_64",
    )


def test_mta_category_unknown(configfile, db, split_layout):
    result = run_command(
        [
            "-c",
            configfile,
            "--repository",
            "free-fedora-updates-released-42",
            "--category",
            "RPMFUSION Fedora",
            "--archive-category",
            "RPMFUSION free Fedora Archive",
        ]
    )
    assert result.exit_code == 2, result.output
    assert "Error: No category could be found by the name: RPMFUSION Fedora" in result.output


def test_mta_category_directory_outside_topdir(configfile, db, split_layout):
    category = mirrormanager2.lib.get_category_by_name(db, "RPMFUSION free Fedora")
    category.topdir = model.Directory(name="free/el", readable=True)
    db.commit()
    result = run_command(
        [
            "-c",
            configfile,
            "--repository",
            "free-fedora-updates-released-42",
            "--category",
            "RPMFUSION free Fedora",
            "--archive-category",
            "RPMFUSION free Fedora Archive",
        ]
    )
    assert result.exit_code == 1, result.output
    assert result.output == (
        "Error: free/fedora/updates/42/x86_64 is not below free/el, "
        "the top directory of [RPMFUSION free Fedora]\n"
    )


def test_mta_bad_version(command_args, base_items, db):
    _make_archive_category(db)
    result = run_command(command_args)

    # Ignore for now
    # assert stderr == ''
    assert result.exit_code == 2
    assert "Error: No such version: 26" in result.output


def test_mta(
    command_args, db, base_items, directory, category, categorydirectory, version, repository
):
    """Test the mta script."""
    result = run_command(command_args)

    assert result.exit_code == 2, result.output
    assert "Error: No category could be found by the name: Fedora Archive" in result.output
    # Ignore for now
    # assert stderr == ''

    # One step further
    _make_archive_category(db)
    results = mirrormanager2.lib.get_repositories(db)
    assert len(results) == 4
    assert results[0].prefix == "updates-testing-f25"
    assert results[0].directory.name == "pub/fedora/linux/updates/testing/25/x86_64"
    assert results[1].prefix == "updates-testing-f26"
    assert results[1].directory.name == "pub/fedora/linux/updates/testing/26/x86_64"
    assert results[2].prefix == "updates-testing-f27"
    assert results[2].directory.name == "pub/fedora/linux/updates/testing/27/x86_64"

    results = db.execute(sa.select(model.Directory)).scalars().all()
    # create_directory creates 9 directories
    # we create 1 more here, 9+1=10
    assert len(results) == 10
    assert results[0].name == "pub/fedora/linux"
    assert results[1].name == "pub/fedora/linux/extras"
    assert results[2].name == "pub/epel"
    assert results[3].name == "pub/fedora/linux/releases/26"
    assert results[4].name == "pub/fedora/linux/releases/27"
    assert results[5].name == "pub/archive/fedora/linux/releases/26/Everything/source"
    assert results[6].name == "pub/fedora/linux/updates/testing/25/x86_64"
    assert results[7].name == "pub/fedora/linux/updates/testing/26/x86_64"
    assert results[8].name == "pub/fedora/linux/updates/testing/27/x86_64"
    assert results[9].name == "pub/archive"

    result = run_command(command_args)
    assert result.output == (
        "Error: Unable to find a directory in [Fedora Archive] for pub/fedora/"
        "linux/updates/testing/26/x86_64\n"
    )
    # Ignore for now
    # assert stderr == ''

    # Run the script so that it works

    item = model.Directory(
        name="pub/archive/fedora/linux/updates/testing/26/x86_64",
        readable=True,
    )
    db.add(item)
    db.commit()

    result = run_command(command_args)
    assert result.output == (
        "pub/fedora/linux/updates/testing/26/x86_64 => "
        "pub/archive/fedora/linux/updates/testing/26/x86_64\n"
    )
    # Ignore for now
    # assert stderr == ''

    results = mirrormanager2.lib.get_repositories(db)
    assert len(results) == 4
    assert results[0].prefix == "updates-testing-f25"
    assert results[0].directory.name == "pub/fedora/linux/updates/testing/25/x86_64"
    assert results[1].prefix == "updates-testing-f26"
    assert results[1].directory.name == "pub/archive/fedora/linux/updates/testing/26/x86_64"
    assert results[2].prefix == "updates-testing-f27"
    assert results[2].directory.name == "pub/fedora/linux/updates/testing/27/x86_64"

    # After the script

    results = db.execute(sa.select(model.Directory)).scalars().all()
    # create_directory creates 9 directories
    # we create 1 more here, 9+1=10
    assert len(results) == 11
    assert results[0].name == "pub/fedora/linux"
    assert results[1].name == "pub/fedora/linux/extras"
    assert results[2].name == "pub/epel"
    assert results[3].name == "pub/fedora/linux/releases/26"
    assert results[4].name == "pub/fedora/linux/releases/27"
    assert results[5].name == "pub/archive/fedora/linux/releases/26/Everything/source"
    assert results[6].name == "pub/fedora/linux/updates/testing/25/x86_64"
    assert results[7].name == "pub/fedora/linux/updates/testing/26/x86_64"
    assert results[8].name == "pub/fedora/linux/updates/testing/27/x86_64"
    assert results[9].name == "pub/archive"
    assert results[10].name == "pub/archive/fedora/linux/updates/testing/26/x86_64"
