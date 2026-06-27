"""Tests for the date normaliser."""

import pytest

from invoice_extractor.parsing import normalize_date


@pytest.mark.parametrize(
    "text, expected",
    [
        # US slash format (month-first)
        ("03/14/2024", "2024-03-14"),
        ("12/31/2023", "2023-12-31"),
        # European dash format (day-first)
        ("18-04-2024", "2024-04-18"),
        ("31-12-2023", "2023-12-31"),
        # European dot format (day-first)
        ("05.03.2024", "2024-03-05"),
        # Worded dates
        ("5 March 2024", "2024-03-05"),
        ("April 2, 2024", "2024-04-02"),
        ("April 2nd, 2024", "2024-04-02"),
        ("2 Apr 2024", "2024-04-02"),
        ("May 2, 2024", "2024-05-02"),
        # Already ISO
        ("2024-03-14", "2024-03-14"),
        # Unambiguous day-first even with slashes (day > 12 forces it)
        ("13/05/2024", "2024-05-13"),
    ],
)
def test_normalize_date(text, expected):
    assert normalize_date(text) == expected


@pytest.mark.parametrize("text", [None, "", "not a date", "2024", "13/13/2024"])
def test_normalize_date_unparseable_returns_none(text):
    assert normalize_date(text) is None


def test_slash_defaults_to_month_first():
    # 05/03 is ambiguous; documented policy is US month-first for slashes.
    assert normalize_date("05/03/2024") == "2024-05-03"


def test_dash_defaults_to_day_first():
    # 05-03 is ambiguous; documented policy is European day-first for dashes.
    assert normalize_date("05-03-2024") == "2024-03-05"
