"""
mirrormanager2 tests for the Jinja template filters.
"""

from datetime import datetime, timedelta, timezone

from mirrormanager2.app import format_datetime


def test_format_datetime_naive():
    value = datetime(2024, 3, 12, 14, 3, 27, 123456)
    assert format_datetime(value) == "2024-03-12 14:03 UTC"


def test_format_datetime_aware_is_converted_to_utc():
    value = datetime(2024, 3, 12, 11, 3, 27, tzinfo=timezone(timedelta(hours=-3)))
    assert format_datetime(value) == "2024-03-12 14:03 UTC"


def test_format_datetime_none():
    assert format_datetime(None) == "-"


def test_format_datetime_registered_as_filter(app):
    template = app.jinja_env.from_string("{{ value | datetime }}")
    assert template.render(value=datetime(2024, 3, 12, 14, 3)) == "2024-03-12 14:03 UTC"
