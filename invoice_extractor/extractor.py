"""The extraction orchestrator.

This module ties everything together: read a PDF's text, locate each field, parse
and normalise it, run the reconciliation check, and emit both the clean
:class:`Invoice` and any :class:`Flag` records.

The design embodies the project's core principle. Each field is processed by a
small helper that returns ``(value, flag_or_none)``. If parsing fails or the
field is absent, ``value`` is ``None`` (blank in the output) and a flag explains
why — the tool never substitutes a guess.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pdfplumber

from . import fields
from .models import ExtractionResult, Flag, Invoice
from .parsing import detect_currency, normalize_date, parse_amount
from .reconcile import reconcile

logger = logging.getLogger(__name__)

# Fields that, when absent, always warrant a review flag. Vendor is excluded
# because it is a heuristic (first line) rather than a labelled field; currency is
# handled separately so we can word its flag precisely.
_FLAG_IF_MISSING = {
    "invoice_number": "Invoice number",
    "customer": "Customer",
    "invoice_date": "Invoice date",
    "due_date": "Due date",
    "subtotal": "Subtotal",
    "total": "Total",
}


def extract_text(pdf_path: Path) -> str:
    """Return the concatenated plain text of every page in a PDF.

    Raises nothing for empty text — a text-free (scanned) PDF yields ""; the
    caller turns that into a clear "no extractable text" flag.
    """
    parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def extract_invoice(pdf_path: Path) -> tuple[Invoice, list[Flag]]:
    """Extract a single invoice PDF into an :class:`Invoice` plus its flags."""
    name = pdf_path.name
    invoice = Invoice(source_file=name)
    flags: list[Flag] = []

    try:
        text = extract_text(pdf_path)
    except Exception as exc:  # pragma: no cover - corrupt/unreadable file
        logger.warning("Could not read %s: %s", name, exc)
        flags.append(Flag(name, "file", f"Could not read PDF: {exc}"))
        return invoice, flags

    if not text.strip():
        # A digital-text extractor cannot do anything with an image-only PDF.
        flags.append(
            Flag(
                name,
                "file",
                "No extractable text found (likely a scanned/image PDF — needs OCR)",
            )
        )
        return invoice, flags

    # --- Text fields ------------------------------------------------------- #
    invoice.vendor = fields.find_vendor(text)
    if not invoice.vendor:
        flags.append(Flag(name, "Vendor", "Vendor name not found"))

    invoice.invoice_number = fields.find_invoice_number(text)
    invoice.customer = fields.find_customer(text)

    # --- Dates ------------------------------------------------------------- #
    invoice.invoice_date = _normalize_date_field(
        name, "Invoice date", fields.find_invoice_date(text), flags
    )
    invoice.due_date = _normalize_date_field(
        name, "Due date", fields.find_due_date(text), flags
    )

    # --- Currency ---------------------------------------------------------- #
    invoice.currency = detect_currency(text)
    if invoice.currency is None:
        flags.append(
            Flag(name, "Currency", "Currency could not be determined or is ambiguous")
        )

    # --- Amounts ----------------------------------------------------------- #
    invoice.subtotal = _parse_amount_field(
        name, "Subtotal", fields.find_subtotal(text), flags, required=True
    )
    invoice.tax = _parse_amount_field(
        name, "Tax / VAT", fields.find_tax(text), flags, required=False
    )
    invoice.total = _parse_amount_field(
        name, "Total", fields.find_total(text), flags, required=True
    )

    # Tax needs nuanced handling: distinguish "not present" from "included in total".
    if invoice.tax is None:
        if fields.has_tax_included_note(text):
            flags.append(
                Flag(
                    name,
                    "Tax / VAT",
                    "Tax appears to be included in the total, not itemised",
                )
            )
        else:
            flags.append(Flag(name, "Tax / VAT", "Tax/VAT amount not found"))

    # --- Flag remaining missing labelled fields ---------------------------- #
    for attr, label in _FLAG_IF_MISSING.items():
        if attr in ("invoice_date", "due_date", "subtotal", "total"):
            continue  # already flagged above with parse-specific reasons
        if getattr(invoice, attr) is None:
            flags.append(Flag(name, label, f"{label} not found"))

    # --- Reconciliation ---------------------------------------------------- #
    mismatch = reconcile(invoice.subtotal, invoice.tax, invoice.total)
    if mismatch:
        flags.append(
            Flag(
                name,
                "Total",
                f"Reconciliation failed: {mismatch}",
                original_text=mismatch,
            )
        )

    return invoice, flags


def extract_folder(folder: Path) -> ExtractionResult:
    """Extract every ``*.pdf`` in ``folder`` (sorted) into an :class:`ExtractionResult`."""
    result = ExtractionResult()
    pdf_paths = sorted(folder.glob("*.pdf"))
    if not pdf_paths:
        logger.warning("No PDF files found in %s", folder)

    for pdf_path in pdf_paths:
        logger.info("Extracting %s", pdf_path.name)
        invoice, flags = extract_invoice(pdf_path)
        result.invoices.append(invoice)
        result.flags.extend(flags)

    return result


# --------------------------------------------------------------------------- #
# Field helpers — each returns the value and appends a flag on failure.
# --------------------------------------------------------------------------- #
def _normalize_date_field(
    source: str, label: str, raw: Optional[str], flags: list[Flag]
) -> Optional[str]:
    if raw is None:
        flags.append(Flag(source, label, f"{label} not found"))
        return None
    iso = normalize_date(raw)
    if iso is None:
        flags.append(
            Flag(source, label, f"{label} could not be parsed", original_text=raw)
        )
    return iso


def _parse_amount_field(
    source: str,
    label: str,
    raw: Optional[str],
    flags: list[Flag],
    *,
    required: bool,
) -> Optional[float]:
    if raw is None:
        if required:
            flags.append(Flag(source, label, f"{label} not found"))
        return None
    value = parse_amount(raw)
    if value is None:
        flags.append(
            Flag(source, label, f"{label} could not be parsed", original_text=raw)
        )
    return value
