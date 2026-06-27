"""Currency detection from invoice text.

We look for either a currency symbol ($, €, £) or an ISO 4217 code (USD, EUR,
GBP). To stay honest, detection returns ``None`` when the evidence is missing or
*conflicting* (e.g. a document containing both ``$`` and ``€``), so the caller
flags it for review instead of picking one arbitrarily.
"""

from __future__ import annotations

import re
from typing import Optional

# Map of recognisable tokens to ISO 4217 codes. The "$" symbol is treated as USD
# here; multi-currency "$" disambiguation (CAD/AUD/etc.) is out of scope and would
# be a flag-worthy ambiguity in a real deployment.
_SYMBOL_TO_CODE = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
}

_CODE_PATTERN = re.compile(r"\b(USD|EUR|GBP)\b", re.IGNORECASE)


def detect_currency(text: Optional[str]) -> Optional[str]:
    """Return the ISO 4217 currency code for ``text``, or ``None`` if unclear.

    Returns ``None`` when no currency evidence is found, or when more than one
    distinct currency is detected (a genuine ambiguity the tool refuses to guess).
    """
    if not text:
        return None

    found: set[str] = set()

    for symbol, code in _SYMBOL_TO_CODE.items():
        if symbol in text:
            found.add(code)

    for match in _CODE_PATTERN.findall(text):
        found.add(match.upper())

    if len(found) == 1:
        return next(iter(found))
    # Zero matches (unknown) or multiple conflicting matches (ambiguous).
    return None
