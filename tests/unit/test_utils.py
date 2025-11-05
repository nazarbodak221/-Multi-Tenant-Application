"""
Unit tests for utility helpers
"""

from datetime import datetime

from app.core.utils import format_datetime


def test_format_datetime_default_format():
    dt = datetime(2025, 1, 2, 3, 4, 5)

    formatted = format_datetime(dt)

    assert formatted == "2025-01-02 03:04:05"


def test_format_datetime_custom_format():
    dt = datetime(2025, 12, 31, 23, 59, 59)

    formatted = format_datetime(dt, "%Y/%m/%d")

    assert formatted == "2025/12/31"


def test_format_datetime_none():
    assert format_datetime(None) is None
