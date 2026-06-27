"""Tests for the locale-aware number parser."""

import pytest

from invoice_extractor.parsing import parse_amount


@pytest.mark.parametrize(
    "text, expected",
    [
        # US style: comma thousands, dot decimal
        ("1,950.00", 1950.00),
        ("$1,950.00", 1950.00),
        ("1,234.56", 1234.56),
        ("12,345,678.90", 12345678.90),
        # European style: dot thousands, comma decimal
        ("1.950,00", 1950.00),
        ("1.234,56", 1234.56),
        ("514,00", 514.00),
        ("€1.468,46", 1468.46),
        # Space-grouped thousands
        ("1 234,56", 1234.56),
        ("1 234 567.89", 1234567.89),
        # Single-separator disambiguation by trailing-digit count
        ("1,950", 1950.0),   # 3 trailing digits -> thousands
        ("1.950", 1950.0),   # 3 trailing digits -> thousands
        ("1.5", 1.5),        # 1 trailing digit -> decimal
        ("12.50", 12.50),    # 2 trailing digits -> decimal
        # Plain integers and currency codes
        ("4820", 4820.0),
        ("USD 4,820.00", 4820.00),
        ("GBP 3,600.00", 3600.00),
        # Sign handling
        ("-25.00", -25.00),
    ],
)
def test_parse_amount_values(text, expected):
    assert parse_amount(text) == pytest.approx(expected)


@pytest.mark.parametrize("text", [None, "", "   ", "n/a", "TBD", "$"])
def test_parse_amount_unparseable_returns_none(text):
    assert parse_amount(text) is None


def test_us_and_eu_disagree_only_on_ambiguous_input():
    # The same digits, different conventions, must not collide silently.
    assert parse_amount("1.234,56") == pytest.approx(1234.56)
    assert parse_amount("1,234.56") == pytest.approx(1234.56)
