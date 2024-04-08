"""
mirrormanager2 tests for the `Update Single File Details` (USFD) cron.
"""

import logging
import os

import pytest
import sqlalchemy as sa
from click.testing import CliRunner

import mirrormanager2.lib
from mirrormanager2.lib import model
from mirrormanager2.utility import update_single_file_detail

FOLDER = os.path.dirname(os.path.abspath(__file__))
UMDL_PREFIX = f"{FOLDER}/../testdata/"
REPOMD_PATH = f"{UMDL_PREFIX}pub/fedora/linux/development/22/x86_64/os/repodata/repomd.xml"


@pytest.fixture()
def configfile(tmp_path):
    path = tmp_path.joinpath("mirrormanager2_tests.cfg").as_posix()
    contents = f"""
SQLALCHEMY_DATABASE_URI = 'sqlite:///{tmp_path.as_posix()}/test.sqlite'
import os
DB_ALEMBIC_LOCATION = os.path.join("{FOLDER}", "..", "mirrormanager2", "lib", "migrations")
UMDL_PREFIX = '{UMDL_PREFIX}'

# Specify whether the crawler should send a report by email
CRAWLER_SEND_EMAIL =  False

UMDL_MASTER_DIRECTORIES = [
    {{
        'type': 'directory',
        'path': '{UMDL_PREFIX}pub/epel/',
        'category': 'Fedora EPEL'
    }},
    {{
        'type': 'directory',
        'path': '{UMDL_PREFIX}pub/fedora/linux/',
        'category': 'Fedora Linux'
    }},
    {{
        'type': 'directory',
        'path': '{UMDL_PREFIX}pub/fedora-secondary/',
        'category': 'Fedora Secondary Arches'
    }},
    {{
        'type': 'directory',
        'path': '{UMDL_PREFIX}pub/archive/',
        'category': 'Fedora Archive'
    }},
    {{
        'type': 'directory',
        'path': '{UMDL_PREFIX}pub/alt/',
        'category': 'Fedora Other'
    }}
]
    """
    with open(path, "w") as stream:
        stream.write(contents)
    return path


@pytest.fixture()
def repomd_directory(db):
    master_dir_prefix = f"{UMDL_PREFIX}pub/fedora/linux/"
    tested_dir = os.path.dirname(REPOMD_PATH)[len(master_dir_prefix) :]
    item = model.Directory(
        name=tested_dir,
        readable=True,
    )
    db.add(item)
    db.commit()
    return item


# testdata/pub/fedora/linux/development/22/x86_64/os/repodata/repomd.xml
# testdata/pub/fedora/linux/releases/20/Fedora/source/SRPMS/repodata/repomd.xml
# testdata/pub/fedora/linux/releases/20/Fedora/x86_64/os/repodata/repomd.xml


@pytest.fixture()
def command_args(configfile):
    return ["-c", configfile]


def run_command(args):
    runner = CliRunner()
    return runner.invoke(update_single_file_detail.main, args)


def test_0_usdf_empty_db(command_args, db, caplog):
    """Test against an empty database."""
    caplog.set_level(logging.DEBUG)
    result = run_command(command_args + [REPOMD_PATH])
    assert result.output == ""
    assert result.exit_code == 0

    # assert result.output == ""
    # Ignore for now
    # assert stderr == ''
    assert caplog.messages == [
        "UMDL_MASTER_DIRECTORIES Category Fedora EPEL does not exist in the database, skipping",
        "UMDL_MASTER_DIRECTORIES Category Fedora Linux does not exist in the database, skipping",
        (
            "UMDL_MASTER_DIRECTORIES Category Fedora Secondary Arches does not exist in the "
            "database, skipping"
        ),
        "UMDL_MASTER_DIRECTORIES Category Fedora Archive does not exist in the database, skipping",
        "UMDL_MASTER_DIRECTORIES Category Fedora Other does not exist in the database, skipping",
        "Done.",
    ]


def test_1_usfd(
    db,
    command_args,
    base_items,
    directory,
    category,
    categorydirectory,
    repomd_directory,
    caplog,
):
    """Test usfd."""
    caplog.set_level(logging.DEBUG)

    result = run_command(command_args + [REPOMD_PATH])
    print(repr(result.exception))
    print(result.exc_info)
    from traceback import print_tb

    print_tb(result.exc_info[2])
    assert result.output == ""
    assert result.exit_code == 0
    # Ignore for now
    # assert stderr == ''

    # tested_dir = "/".join(REPOMD_PATH.split("/")[2:-1])
    print(caplog.records)
    print(caplog.text)
    assert caplog.messages == [
        (
            "UMDL_MASTER_DIRECTORIES Category Fedora Secondary Arches does not exist in the "
            "database, skipping"
        ),
        "UMDL_MASTER_DIRECTORIES Category Fedora Archive does not exist in the database, skipping",
        "UMDL_MASTER_DIRECTORIES Category Fedora Other does not exist in the database, skipping",
        "Considering category Fedora Linux",
        f"Updating FileDetail 1 for {REPOMD_PATH!r}",
        "Done.",
    ]

    # The DB should now be filled with what USFD added, so let's check it

    results = db.execute(sa.select(model.Directory)).scalars().all()
    assert len(results) == 10
    # Added by repomd_directory
    assert results[-1].id == repomd_directory.id

    results = db.execute(sa.select(model.FileDetail)).scalars().all()
    assert len(results) == 1

    result = mirrormanager2.lib.get_file_detail(db, filename="repomd.xml", directory_id=10)
    assert result is not None
    assert result.filename == "repomd.xml"
    print(result.sha1, result.md5, result.sha256, result.sha512, result.size)
    assert result.sha1 == "fffc4fc6657712757cba01a84c1e538d65afa88b"
    assert result.md5 == "d0fb87891c3bfbdaf7a225f57e9ba6ee"
    assert result.sha256 == "860f0f832f7a641cf8f7e27172ef9b2492ce849388e43f372af7e512aa646677"
    assert result.sha512 == (
        "7bb9a0bae076ccbbcd086163a1d4f33b62321aa6991d135c42bf3f6c42c4eb465a0b42c62efa"
        "809708543fcd69511cb19cd7111d5ff295a50253b9c7659bb9d6"
    )
    assert result.size == 3732
