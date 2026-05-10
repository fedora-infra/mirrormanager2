"""
mirrormanager2 tests for the netblocks utility.
"""

import bz2
import os
import re
import tempfile
from io import BytesIO

import pytest
import requests
from click.testing import CliRunner

from mirrormanager2.utility.netblocks import main


@pytest.fixture(autouse=True)
def setup_all():
    skip = os.getenv("MM2_SKIP_NETWORK_TESTS", 0)
    if skip:
        raise pytest.skip("Skipping netblocks tests")


FOLDER = os.path.dirname(os.path.abspath(__file__))
GLOBAL_NETBLOCKS_URL = "http://ftp.routeviews.org/dnszones/rib.bz2"
IPV6_NETBLOCKS_URL = (
    "http://archive.routeviews.org/route-views6/bgpdata/2025.11/RIBS/rib.20251101.0000.bz2"
)


def create_test_bgp_data():
    """Download BGP data and create a test file with first 100,000 bytes."""
    print("Downloading BGP test data...")

    # Download the BGP data
    response = requests.get(GLOBAL_NETBLOCKS_URL, timeout=120)
    response.raise_for_status()

    # Decompress, take first 100,000 bytes, then recompress
    with bz2.open(BytesIO(response.content)) as content:
        first_100k = content.read(100000)

    # Create temporary file for the test data
    temp_file = tempfile.NamedTemporaryFile(prefix="bgp_test_", suffix=".bz2", delete=False)

    with bz2.open(temp_file.name, "wb") as compressed_file:
        compressed_file.write(first_100k)

    return temp_file.name


def create_test_ipv6_bgp_data():
    """Download IPv6 BGP data and create a test file with first 100,000 bytes."""
    print("Downloading IPv6 BGP test data...")

    # Download the IPv6 BGP data
    response = requests.get(IPV6_NETBLOCKS_URL, timeout=120)
    response.raise_for_status()

    # Decompress, take first 100,000 bytes, then recompress
    with bz2.open(BytesIO(response.content)) as content:
        first_100k = content.read(100000)

    # Create temporary file for the test data
    temp_file = tempfile.NamedTemporaryFile(prefix="bgp_ipv6_test_", suffix=".bz2", delete=False)

    with bz2.open(temp_file.name, "wb") as compressed_file:
        compressed_file.write(first_100k)

    return temp_file.name


def test_global_netblocks_with_local_file_disable_ipv6():
    """Test global netblocks processing with local file and IPv6 disabled."""
    runner = CliRunner()

    # Create test BGP data dynamically
    test_global_file = create_test_bgp_data()

    # Create temporary output file
    output_file = tempfile.NamedTemporaryFile(
        prefix="netblocks_output_", suffix=".txt", delete=False
    )
    output_file.close()  # Close so the CLI can write to it

    try:
        # Run the netblocks command with local global file and IPv6 disabled
        result = runner.invoke(
            main, ["global", output_file.name, "--global-file", test_global_file, "--disable-ipv6"]
        )

        # Verify the command ran successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Verify the output file was created and has content
        assert os.path.exists(output_file.name), "Output file was not created"

        # Read and verify the output content
        with open(output_file.name) as f:
            content = f.read()

        lines = content.strip().split("\n")

        # Filter out empty lines
        lines = [line for line in lines if line.strip()]

        # Verify we have at least 50 entries (based on our test data size)
        assert len(lines) >= 50, f"Expected at least 50 entries, got {len(lines)}"

        # Verify format: <ipv4 prefix>/length <AS number>
        # Pattern matches IPv4 prefix/length followed by AS number
        ipv4_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}\s+\d+$")

        valid_entries = 0
        for line in lines:
            if ipv4_pattern.match(line.strip()):
                valid_entries += 1

        # Verify that most entries match the expected format
        # Allow some flexibility as BGP data might contain some variations
        assert valid_entries >= 40, f"Expected at least 40 valid IPv4 entries, got {valid_entries}"

        # Verify output contains global processing message and no IPv6 message
        assert "Processing global netblocks" in result.output
        assert "IPv6 netblocks: DISABLED" in result.output
        assert "Processing IPv6 netblocks" not in result.output

    finally:
        # Clean up temporary files
        try:
            os.unlink(test_global_file)
        except OSError:
            pass
        try:
            os.unlink(output_file.name)
        except OSError:
            pass


def test_ipv6_netblocks_with_local_file_disable_global():
    """Test IPv6 netblocks processing with local file and global disabled."""
    runner = CliRunner()

    # Create test IPv6 BGP data dynamically
    test_ipv6_file = create_test_ipv6_bgp_data()

    # Create temporary output file
    output_file = tempfile.NamedTemporaryFile(
        prefix="netblocks_ipv6_output_", suffix=".txt", delete=False
    )
    output_file.close()  # Close so the CLI can write to it

    try:
        # Run the netblocks command with local IPv6 file and global disabled
        result = runner.invoke(
            main, ["global", output_file.name, "--ipv6-file", test_ipv6_file, "--disable-global"]
        )

        # Verify the command ran successfully
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Verify the output file was created and has content
        assert os.path.exists(output_file.name), "Output file was not created"

        # Read and verify the output content
        with open(output_file.name) as f:
            content = f.read()

        lines = content.strip().split("\n")

        # Filter out empty lines
        lines = [line for line in lines if line.strip()]

        # Verify we have at least 30 entries (IPv6 data might be sparser)
        assert len(lines) >= 30, f"Expected at least 30 entries, got {len(lines)}"

        # Verify format: <ipv6 prefix>/length <AS number>
        # Pattern matches IPv6 prefix/length followed by AS number
        # IPv6 addresses contain colons and can have compressed notation (::)
        ipv6_pattern = re.compile(r"^[0-9a-fA-F:]+/\d{1,3}\s+\d+$")

        valid_entries = 0
        for line in lines:
            if ipv6_pattern.match(line.strip()):
                valid_entries += 1

        # Verify that most entries match the expected format
        # Allow some flexibility as BGP data might contain some variations
        assert valid_entries >= 20, f"Expected at least 20 valid IPv6 entries, got {valid_entries}"

        # Verify output contains IPv6 processing message and no global message
        assert "Processing IPv6 netblocks" in result.output
        assert "Global netblocks: DISABLED" in result.output
        assert "Processing global netblocks" not in result.output

    finally:
        # Clean up temporary files
        try:
            os.unlink(test_ipv6_file)
        except OSError:
            pass
        try:
            os.unlink(output_file.name)
        except OSError:
            pass


def test_netblocks_disable_both_fails():
    """Test that disabling both global and IPv6 fails with proper error."""
    runner = CliRunner()

    # Create temporary output file (even though it won't be used due to error)
    output_file = tempfile.NamedTemporaryFile(prefix="test_netblocks_", suffix=".txt", delete=False)
    output_file.close()

    try:
        result = runner.invoke(
            main, ["global", output_file.name, "--disable-global", "--disable-ipv6"]
        )

        # Should fail with error about disabling both
        assert result.exit_code != 0
        assert "Cannot disable both global and IPv6 processing" in result.output

    finally:
        # Clean up temporary file
        try:
            os.unlink(output_file.name)
        except OSError:
            pass


def test_netblocks_help_shows_new_options():
    """Test that help output shows the new disable options."""
    runner = CliRunner()

    result = runner.invoke(main, ["global", "--help"])

    assert result.exit_code == 0
    assert "--disable-global" in result.output
    assert "--disable-ipv6" in result.output
    assert "Skip global netblocks processing" in result.output
    assert "Skip IPv6 netblocks processing" in result.output
