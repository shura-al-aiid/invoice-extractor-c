"""Date normalisation to ISO ``YYYY-MM-DD``.

Invoices use many date styles. We normalise the common ones to ISO. The tricky
case is purely numeric dates such as ``05/03/2024`` which are ambiguous between
US (month-first) and European (day-first) order. Rather than guess invisibly we
apply documented per-separator conventions, but still recover an unambiguous date
when one component is clearly out of range (``13/05/2024`` can only be day-first).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

# Ordered list of accepted formats. Order encodes our disambiguation policy:
#   * named-month and ISO formats first  (unambiguous)
#   * "/" separated  -> assume US month-first, then fall back to day-first
#   * "-" separated  -> assume European day-first, then fall back to month-first
#   * "." separated  -> assume European day-first
# strptime rejects impossible dates (e.g. month 13), so a clearly day-first value
# written with slashes still parses via the fallback format.
_FORMATS: tuple[str, ...] = (
    # ISO and named months (unambiguous)
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d %B %Y", "%d %b %Y",
    "%d %B, %Y", "%d %b, %Y",
    "%B %d, %Y", "%b %d, %Y",
    "%B %d %Y", "%b %d %Y",
    # Slash: US month-first preferred, day-first fallback
    "%m/%d/%Y", "%m/%d/%y",
    "%d/%m/%Y", "%d/%m/%y",
    # Dash: European day-first preferred, month-first fallback
    "%d-%m-%Y", "%d-%m-%y",
    "%m-%d-%Y", "%m-%d-%y",
    # Dot: European day-first
    "%d.%m.%Y", "%d.%m.%y",
)


def normalize_date(text: Optional[str]) -> Optional[str]:
    """Return ``text`` as an ISO ``YYYY-MM-DD`` string, or ``None`` if unparseable.

    Trailing ordinal suffixes ("1st", "2nd", "3rd", "4th") are tolerated so that
    "April 2nd, 2024" parses. Whitespace and stray commas are normalised first.
    """
    if not text:
        return None

    candidate = _clean(text)
    if not candidate:
        return None

    for fmt in _FORMATS:
        try:
            parsed = datetime.strptime(candidate, fmt)
        except ValueError:
            continue
        return parsed.strftime("%Y-%m-%d")
    return None


def _clean(text: str) -> str:
    """Strip ordinal suffixes and collapse whitespace for strptime."""
    import re

    cleaned = text.strip()
    # Remove ordinal suffixes attached to day numbers: 1st, 2nd, 3rd, 4th ...
    cleaned = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", cleaned, flags=re.IGNORECASE)
    # Collapse internal runs of whitespace to a single space.
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned
