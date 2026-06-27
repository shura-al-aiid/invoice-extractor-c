"""Tests for currency detection."""

import pytest

from invoice_extractor.parsing import detect_currency


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Total Due: $2,115.75", "USD"),
        ("Amount Payable: €1.468,46", "EUR"),
        ("Balance Due: £3,600.00", "GBP"),
        ("Total: USD 4,820.00", "USD"),
        ("Subtotal EUR 1.234,00", "EUR"),
        ("Price in GBP only", "GBP"),
    ],
)
def test_detect_currency(text, expected):
    assert detect_currency(text) == expected


@pytest.mark.parametrize("text", [None, "", "no currency here", "1,950.00"])
def test_detect_currency_none_when_absent(text):
    assert detect_currency(text) is None


def test_detect_currency_none_when_ambiguous():
    # Two different currencies present -> refuse to guess.
    assert detect_currency("Subtotal $100 then converted to €92") is None
