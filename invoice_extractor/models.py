"""Data models shared across the package.

These light-weight dataclasses are the contract between the extraction layer
(which produces them) and the output layer (which serialises them). Keeping them
in one place means the column order, field names, and flag shape are defined
exactly once.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Optional


# The canonical, human-readable column order for the "Extracted Invoices" sheet.
# The keys are the dataclass attribute names; the values are the column headers.
INVOICE_COLUMNS: dict[str, str] = {
    "source_file": "Source File",
    "vendor": "Vendor",
    "invoice_number": "Invoice Number",
    "customer": "Customer",
    "invoice_date": "Invoice Date",
    "due_date": "Due Date",
    "currency": "Currency",
    "subtotal": "Subtotal",
    "tax": "Tax / VAT",
    "total": "Total",
}


@dataclass
class Invoice:
    """One extracted invoice — one row in the clean output table.

    Every field except ``source_file`` is optional. A value of ``None`` means
    "not confidently extracted" and is rendered as a blank cell; the reason it is
    blank lives in the associated :class:`Flag` records.
    """

    source_file: str
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    customer: Optional[str] = None
    invoice_date: Optional[str] = None  # ISO YYYY-MM-DD
    due_date: Optional[str] = None      # ISO YYYY-MM-DD
    currency: Optional[str] = None      # ISO 4217 code, e.g. "USD"
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None

    def as_row(self) -> list:
        """Return the invoice as a list of cell values in canonical column order."""
        return [getattr(self, name) for name in INVOICE_COLUMNS]

    @staticmethod
    def headers() -> list[str]:
        """Return the column headers in canonical order."""
        return list(INVOICE_COLUMNS.values())


@dataclass
class Flag:
    """A single item that needs human review.

    One row in the "Flagged for Review" sheet. ``original_text`` captures the raw
    snippet (when available) so a reviewer can resolve the issue without reopening
    the source PDF.
    """

    source_file: str
    field: str
    issue: str
    original_text: str = ""

    def as_row(self) -> list:
        return [self.source_file, self.field, self.issue, self.original_text]

    @staticmethod
    def headers() -> list[str]:
        return ["Source File", "Field", "Issue", "Original Text"]


@dataclass
class ExtractionResult:
    """The complete result of processing a folder of invoices.

    Holds the clean invoice rows and the flags raised while producing them. The
    output layer consumes this object directly.
    """

    invoices: list[Invoice] = field(default_factory=list)
    flags: list[Flag] = field(default_factory=list)

    # ------------------------------------------------------------------ summary
    @property
    def invoice_count(self) -> int:
        return len(self.invoices)

    @property
    def flag_count(self) -> int:
        return len(self.flags)

    def fields_filled(self, invoice: Invoice) -> int:
        """Count how many of the extractable fields were populated for an invoice.

        ``source_file`` is excluded — it is always present and is not "extracted".
        """
        data_fields = [f.name for f in fields(Invoice) if f.name != "source_file"]
        return sum(getattr(invoice, name) is not None for name in data_fields)

    @property
    def extractable_field_count(self) -> int:
        """Number of fields we attempt to extract per invoice (excludes source)."""
        return len([f for f in fields(Invoice) if f.name != "source_file"])
