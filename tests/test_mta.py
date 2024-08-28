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
def configfile(tmp_path):
    path = tmp_path.joinpath("mirrormanager2_tests.cfg").as_posix()
    contents = f"""
SQLALCHEMY_DATABASE_URI = 'sqlite:///{tmp_path.as_posix()}/test.sqlite'
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
