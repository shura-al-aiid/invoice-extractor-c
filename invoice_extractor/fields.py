"""Field-level extraction from raw invoice text.

Each public ``find_*`` function takes the full plain text of an invoice and
returns the raw matched string (or ``None``). Parsing/normalisation of those raw
strings happens later, so these functions stay focused on *locating* values
across the many ways invoices label them.

The label vocabularies below are intentionally broad — they are the heart of
handling "real-world variation" — but every pattern is anchored to a label so we
never scrape a random number off the page.
"""

from __future__ import annotations

import re
from typing import Optional

# A monetary value: optional currency symbol or ISO code, then digits with
# separators. Captures the value including its symbol/code; parse_amount() strips
# the currency noise and detect_currency() reads it separately.
_AMOUNT = r"((?:US\$|USD|EUR|GBP|[$€£])?\s*-?\d[\d.,\s]*\d|\d)"

# A date in any of the styles we normalise. Kept permissive; normalize_date()
# validates and rejects nonsense, so a loose capture here is safe.
_DATE = (
    r"("
    r"\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}"          # 05/03/2024, 5-3-24, 5.3.2024
    r"|\d{4}-\d{2}-\d{2}"                          # ISO 2024-03-05
    r"|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4}"  # 5 March 2024
    r"|[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"  # April 2, 2024
    r")"
)


# Default separator between a label and its value: an optional punctuation mark
# (:, #, -, or .) with surrounding whitespace (including a line break). The "."
# lets "Invoice No. CH-1042" match after the abbreviation's trailing period.
_DEFAULT_GAP = r"\s*[.:#\-]?\s*"

# Amount separator: as above but also tolerates an inline rate annotation such as
# "(8.5%)" or "@ 20%" that often sits between a tax/total label and the figure.
_AMOUNT_GAP = r"\s*(?:\([^)]*\))?\s*(?:@?\s*\d+(?:\.\d+)?\s*%)?\s*[:#\-]?\s*"


def _search_label(
    text: str, labels: list[str], value: str, gap: str = _DEFAULT_GAP
) -> Optional[str]:
    """Return the first ``value`` capture that follows any of ``labels``.

    ``labels`` are regex fragments. ``gap`` is the separator pattern allowed
    between a label and its value (default: optional colon/hash/dash and
    whitespace, including a line break, so "Invoice No.\\nINV-001" still matches).
    Matching is case-insensitive.
    """
    for label in labels:
        pattern = re.compile(
            label + gap + value,
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            captured = match.group(1).strip()
            if captured:
                return captured
    return None


# --------------------------------------------------------------------------- #
# Identifiers and parties
# --------------------------------------------------------------------------- #
def find_invoice_number(text: str) -> Optional[str]:
    """Locate the invoice number across varied labels.

    Handles "Invoice #", "Invoice No.", "Invoice Number", "INVOICE 0042", and
    "REF:". The value is an alphanumeric token that may contain dashes or slashes.
    """
    token = r"([A-Za-z0-9][A-Za-z0-9\-/]*)"
    # The abbreviations end in \b so "No." does not match the "No" in "Northwind".
    labels = [
        r"invoice\s*(?:#|no\.?\b|number\b|num\.?\b)",
        r"\bref\.?\b",
        r"\binvoice\b",  # bare "INVOICE 0042" — tried last as it is least specific
    ]
    return _search_label(text, labels, token)


def find_vendor(text: str) -> Optional[str]:
    """Best-effort vendor (issuer) name.

    Most invoices print the issuing company as the first non-empty line, so that
    is our heuristic. A standalone decorative "INVOICE" title (common at the top
    of the page) is stripped so it does not contaminate the name.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Drop a leading/trailing "INVOICE" / "INVOICE 0042" decoration.
        cleaned = re.sub(
            r"^\s*invoice\b\s*#?\s*\d*\s*|\s*\binvoice\b\s*#?\s*\d*\s*$",
            "",
            stripped,
            flags=re.IGNORECASE,
        ).strip()
        # If the line was *only* the title, skip to the next real line.
        if cleaned:
            return cleaned
    return None


def find_customer(text: str) -> Optional[str]:
    """Locate the customer/bill-to name.

    Captures the text on the line *after* a bill-to style label, which is where
    invoices almost always put the customer name.
    """
    labels = [
        r"bill(?:ed)?\s*to",
        r"sold\s*to",
        r"\bcustomer\b",
        r"\bclient\b",
        r"invoice\s*to",
    ]
    # Customer name typically sits on the next line after the label.
    for label in labels:
        pattern = re.compile(
            label + r"\s*:?\s*\n\s*([^\n]+)",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    # Fallback: same-line "Customer: Acme Ltd".
    return _search_label(text, labels, r"([^\n]+)")


# --------------------------------------------------------------------------- #
# Dates
# --------------------------------------------------------------------------- #
def find_invoice_date(text: str) -> Optional[str]:
    """Locate the raw invoice/issue date string."""
    labels = [
        r"invoice\s*date",
        r"date\s*of\s*issue",
        r"\bissued?\b",
        # generic "Date:" — least specific, tried last. The negative lookbehind
        # stops it matching the "Date" in "Due Date", which would otherwise pull
        # the due date in as the invoice date on invoices that lack an explicit
        # "Invoice Date" label.
        r"(?<!due\s)\bdate\b",
    ]
    return _search_label(text, labels, _DATE)


def find_due_date(text: str) -> Optional[str]:
    """Locate the raw due date string."""
    labels = [
        r"due\s*date",
        r"date\s*due",
        r"payment\s*due",
        r"\bdue\b",
    ]
    return _search_label(text, labels, _DATE)


# --------------------------------------------------------------------------- #
# Amounts
# --------------------------------------------------------------------------- #
def find_subtotal(text: str) -> Optional[str]:
    labels = [r"sub[\s\-]*total", r"\bnet\s*(?:amount|total)?\b"]
    return _search_label(text, labels, _AMOUNT, gap=_AMOUNT_GAP)


def find_tax(text: str) -> Optional[str]:
    """Locate a tax/VAT amount.

    Note the patterns require a tax *amount* to follow the label. An invoice that
    only says "price includes VAT" has no itemised figure here and will correctly
    return ``None`` — the extractor turns that into a review flag.
    """
    labels = [
        r"\bvat\b",        # rate annotations like "VAT (19%)" handled by the gap
        r"\bsales\s*tax\b",
        r"\bgst\b",
        r"\btax\b",
    ]
    return _search_label(text, labels, _AMOUNT, gap=_AMOUNT_GAP)


def find_total(text: str) -> Optional[str]:
    """Locate the grand total across its many phrasings.

    More specific phrases ("Total Due", "Amount Payable", "Balance Due") are
    matched before the bare "Total" so we prefer the final payable figure.
    """
    labels = [
        r"total\s*due",
        r"amount\s*payable",
        r"balance\s*due",
        r"amount\s*due",
        r"grand\s*total",
        r"\btotal\b",
    ]
    return _search_label(text, labels, _AMOUNT, gap=_AMOUNT_GAP)


def has_tax_included_note(text: str) -> bool:
    """Detect language indicating tax is folded into the total, not itemised.

    e.g. "Price includes VAT @ 20%", "incl. VAT", "tax included". Used to give the
    reviewer a precise reason rather than a generic "tax missing".
    """
    patterns = [
        r"incl(?:uding|\.|udes)?\s+(?:vat|tax|gst)",
        r"(?:vat|tax|gst)\s+included",
        r"price\s+includes\s+(?:vat|tax|gst)",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)
