"""Locale-aware monetary number parsing.

Invoices in the wild mix US and European conventions:

    US style:        1,950.00   (comma = thousands, dot = decimal)
    European style:  1.950,00   (dot = thousands, comma = decimal)
    European short:  514,00     (comma = decimal)
    Spaced:          1 234,56   (space = thousands, comma = decimal)

The job of :func:`parse_amount` is to turn any of these into a Python ``float``
without ever silently mis-reading one convention as the other. Where a string is
genuinely ambiguous (e.g. ``1,950`` could be 1950 or 1.95) we apply one clearly
documented rule rather than a hidden guess, and the caller can decide whether the
result is trustworthy.
"""

from __future__ import annotations

import re
from typing import Optional

# Characters we accept as part of a number once currency symbols are stripped.
_ALLOWED = re.compile(r"[0-9.,\s]")
# Currency symbols / codes commonly glued to amounts. Removed before parsing.
_CURRENCY_NOISE = re.compile(r"[$€£]|USD|EUR|GBP|US\$", re.IGNORECASE)


def parse_amount(text: Optional[str]) -> Optional[float]:
    """Parse a monetary string into a float, or return ``None`` if not parseable.

    The decimal separator is determined as follows:

    * If both ``.`` and ``,`` appear, the **last one to appear** is the decimal
      separator and the other is the thousands separator
      (``1.950,00`` -> 1950.00, ``1,950.00`` -> 1950.00).
    * If only one separator appears, it is treated as a **decimal point** when it
      is followed by exactly one or two digits (``514,00`` -> 514.0,
      ``1.5`` -> 1.5) and as a **thousands separator** when followed by exactly
      three digits (``1,950`` -> 1950.0, ``1.950`` -> 1950.0). This single rule
      is the only ambiguity-resolving assumption in the parser.
    * Spaces are always thousands separators.

    Returns ``None`` for empty input or anything without a digit, so the caller
    can flag it rather than receive a fabricated zero.
    """
    if text is None:
        return None

    # Remove currency symbols/codes and surrounding whitespace.
    cleaned = _CURRENCY_NOISE.sub("", text).strip()

    # Detect a leading sign, then keep only number-relevant characters.
    negative = cleaned.startswith("-")
    cleaned = "".join(ch for ch in cleaned if _ALLOWED.match(ch))
    cleaned = cleaned.strip()
    if not any(ch.isdigit() for ch in cleaned):
        return None

    # Spaces only ever group thousands.
    cleaned = cleaned.replace(" ", "")

    has_dot = "." in cleaned
    has_comma = "," in cleaned

    if has_dot and has_comma:
        # Whichever separator appears last is the decimal separator.
        if cleaned.rfind(".") > cleaned.rfind(","):
            normalized = cleaned.replace(",", "")          # comma = thousands
        else:
            normalized = cleaned.replace(".", "").replace(",", ".")  # dot = thousands
    elif has_comma:
        normalized = _resolve_single_separator(cleaned, ",")
    elif has_dot:
        normalized = _resolve_single_separator(cleaned, ".")
    else:
        normalized = cleaned

    try:
        value = float(normalized)
    except ValueError:
        return None
    return -value if negative else value


def _resolve_single_separator(text: str, sep: str) -> str:
    """Resolve a number containing exactly one kind of separator.

    Two or more occurrences of the separator => it must be a thousands grouping
    (e.g. ``1,234,567``). A single occurrence is decimal when it groups 1-2
    trailing digits and thousands when it groups exactly 3.
    """
    if text.count(sep) > 1:
        return text.replace(sep, "")

    integer_part, _, fraction = text.partition(sep)
    if len(fraction) == 3 and integer_part:
        # Three trailing digits -> thousands separator (e.g. 1,950 -> 1950).
        return integer_part + fraction
    # One or two (or zero) trailing digits -> decimal separator.
    return integer_part + "." + fraction
