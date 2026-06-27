"""Arithmetic reconciliation of extracted amounts.

When subtotal, tax, and total are all present we can sanity-check the extraction:
``subtotal + tax`` should equal ``total``. A mismatch usually means a number was
misread (wrong line picked up, decimal mis-parsed), so we surface it for review
rather than trusting it.
"""

from __future__ import annotations

from typing import Optional

# Absolute tolerance in currency units. Covers benign rounding (e.g. per-line
# rounding that differs from rounding the summed total) without hiding real errors.
DEFAULT_TOLERANCE = 0.01


def reconcile(
    subtotal: Optional[float],
    tax: Optional[float],
    total: Optional[float],
    tolerance: float = DEFAULT_TOLERANCE,
) -> Optional[str]:
    """Check that ``subtotal + tax == total`` within ``tolerance``.

    Returns ``None`` when the numbers reconcile (or when any value is missing, in
    which case there is nothing to check). When they do not reconcile, returns a
    human-readable explanation string suitable for use as a flag ``issue``.
    """
    if subtotal is None or tax is None or total is None:
        return None  # Incomplete data — not a reconciliation failure.

    expected = subtotal + tax
    # The small epsilon absorbs binary floating-point noise so a difference of
    # exactly `tolerance` (e.g. one cent) is not rejected by representation error.
    if abs(expected - total) <= tolerance + 1e-9:
        return None

    return (
        f"subtotal ({subtotal:.2f}) + tax ({tax:.2f}) = {expected:.2f}, "
        f"but total is {total:.2f}"
    )
