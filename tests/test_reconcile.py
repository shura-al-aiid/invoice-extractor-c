"""Tests for the reconciliation check (subtotal + tax == total)."""

from invoice_extractor.reconcile import reconcile


def test_reconcile_passes_when_balanced():
    assert reconcile(1950.00, 165.75, 2115.75) is None


def test_reconcile_passes_within_tolerance():
    # One cent of rounding noise is tolerated.
    assert reconcile(100.00, 7.00, 107.01) is None


def test_reconcile_fails_on_mismatch():
    message = reconcile(1000.00, 100.00, 1500.00)
    assert message is not None
    assert "1500.00" in message  # reports the offending total


def test_reconcile_skipped_when_any_value_missing():
    assert reconcile(None, 100.00, 1100.00) is None
    assert reconcile(1000.00, None, 1100.00) is None
    assert reconcile(1000.00, 100.00, None) is None


def test_reconcile_respects_custom_tolerance():
    # A 5-cent gap fails at the default 1-cent tolerance...
    assert reconcile(100.00, 0.00, 100.05) is not None
    # ...but passes when the tolerance is widened.
    assert reconcile(100.00, 0.00, 100.05, tolerance=0.10) is None
