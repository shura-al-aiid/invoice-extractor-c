"""Pure, well-tested parsing helpers.

These functions are deliberately free of any PDF or I/O concerns so they can be
unit-tested in isolation — they are the trickiest part of the tool and the part a
reviewing client is most likely to scrutinise.
"""

from .numbers import parse_amount
from .dates import normalize_date
from .currency import detect_currency

__all__ = ["parse_amount", "normalize_date", "detect_currency"]
