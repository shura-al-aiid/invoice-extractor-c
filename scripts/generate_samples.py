"""Generate four fictional sample invoice PDFs for demonstration.

Run this once so the project works out of the box:

    python scripts/generate_samples.py

Each invoice deliberately uses a DIFFERENT layout, currency, date format, and
number style so the extractor's real-world handling is visible. Two are crafted to
trigger the review-flagging system:

  * "Zenith Furniture Works"  — has NO due date (missing-field flag)
  * "Crownsmith & Hart Ltd"   — tax is INCLUDED in the total, not itemised

IMPORTANT: every vendor, customer, address, and figure below is INVENTED for
demonstration only. None of this is real client or company data.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# Output directory (repo_root/sample_invoices), resolved relative to this file.
SAMPLES_DIR = Path(__file__).resolve().parent.parent / "sample_invoices"


# --------------------------------------------------------------------------- #
# Small drawing helpers
# --------------------------------------------------------------------------- #
def _text(c: canvas.Canvas, x: float, y: float, s: str, font="Helvetica", size=10):
    c.setFont(font, size)
    c.drawString(x, y, s)


def _right(c: canvas.Canvas, x: float, y: float, s: str, font="Helvetica", size=10):
    c.setFont(font, size)
    c.drawRightString(x, y, s)


def _center(c: canvas.Canvas, x: float, y: float, s: str, font="Helvetica", size=10):
    c.setFont(font, size)
    c.drawCentredString(x, y, s)


# A note on layout: distinct fields are never placed at the same vertical
# position. PDF text extraction groups characters into lines by their y-position,
# so two fields sharing a y would be merged into one ambiguous line. Real invoices
# often do exactly that (multi-column headers); handling that robustly is noted in
# the project's roadmap. The "totals" block intentionally keeps each label and its
# amount on the same line — that is a single field/value pair the extractor expects.


# --------------------------------------------------------------------------- #
# Invoice 1 — US tech vendor: USD, MM/DD/YYYY, itemised tax, "Invoice #"
# --------------------------------------------------------------------------- #
def invoice_one(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=LETTER)
    w, h = LETTER

    _center(c, w / 2, h - 22 * mm, "INVOICE", "Helvetica-Bold", 22)

    _text(c, 25 * mm, h - 38 * mm, "Northwind Cloud Systems", "Helvetica-Bold", 16)
    _text(c, 25 * mm, h - 45 * mm, "1200 Harbor Ave, Seattle, WA 98101")
    _text(c, 25 * mm, h - 50 * mm, "billing@northwindcloud.example")

    _text(c, 25 * mm, h - 64 * mm, "Invoice #: NW-2024-0118")
    _text(c, 25 * mm, h - 70 * mm, "Invoice Date: 03/14/2024")
    _text(c, 25 * mm, h - 76 * mm, "Due Date: 04/13/2024")

    _text(c, 25 * mm, h - 90 * mm, "Bill To:", "Helvetica-Bold")
    _text(c, 25 * mm, h - 96 * mm, "Acme Robotics Inc.")
    _text(c, 25 * mm, h - 101 * mm, "55 Innovation Way, Austin, TX 78701")

    y = h - 120 * mm
    _text(c, 25 * mm, y, "Description", "Helvetica-Bold")
    _right(c, w - 25 * mm, y, "Amount", "Helvetica-Bold")
    c.line(25 * mm, y - 2 * mm, w - 25 * mm, y - 2 * mm)
    y -= 10 * mm
    for desc, amt in [
        ("Managed Kubernetes — March", "$1,450.00"),
        ("Object storage (2 TB)", "$500.00"),
    ]:
        _text(c, 25 * mm, y, desc)
        _right(c, w - 25 * mm, y, amt)
        y -= 7 * mm

    y -= 6 * mm
    _right(c, w - 25 * mm, y, "Subtotal: $1,950.00")
    y -= 6 * mm
    _right(c, w - 25 * mm, y, "Sales Tax (8.5%): $165.75")
    y -= 8 * mm
    _right(c, w - 25 * mm, y, "Total Due: $2,115.75", "Helvetica-Bold", 11)

    _text(c, 25 * mm, 25 * mm, "Thank you for your business.")
    c.save()


# --------------------------------------------------------------------------- #
# Invoice 2 — European vendor: EUR, worded date, EU numbers, "REF:", NO due date
# --------------------------------------------------------------------------- #
def invoice_two(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4

    _text(c, 20 * mm, h - 22 * mm, "Zenith Furniture Works", "Helvetica-Bold", 16)
    _text(c, 20 * mm, h - 28 * mm, "Industriestrasse 14, 10115 Berlin, Germany")
    _text(c, 20 * mm, h - 33 * mm, "konto@zenithfurniture.example")

    _text(c, 20 * mm, h - 48 * mm, "REF: ZM-00457", "Helvetica-Bold", 11)
    _text(c, 20 * mm, h - 55 * mm, "Invoice Date: 5 March 2024")
    # NOTE: deliberately NO due date on this invoice.

    _text(c, 20 * mm, h - 69 * mm, "Bill To:", "Helvetica-Bold")
    _text(c, 20 * mm, h - 75 * mm, "Cafe Lumiere SARL")
    _text(c, 20 * mm, h - 80 * mm, "8 Rue des Lilas, 75011 Paris, France")

    y = h - 100 * mm
    _text(c, 20 * mm, y, "Position", "Helvetica-Bold")
    _right(c, w - 20 * mm, y, "Betrag", "Helvetica-Bold")
    c.line(20 * mm, y - 2 * mm, w - 20 * mm, y - 2 * mm)
    y -= 10 * mm
    for desc, amt in [
        ("Oak conference table", "EUR 980,00"),
        ("Upholstered chairs (x6)", "EUR 254,00"),
    ]:
        _text(c, 20 * mm, y, desc)
        _right(c, w - 20 * mm, y, amt)
        y -= 7 * mm

    y -= 6 * mm
    _right(c, w - 20 * mm, y, "Subtotal: EUR 1.234,00")
    y -= 6 * mm
    _right(c, w - 20 * mm, y, "VAT (19%): EUR 234,46")
    y -= 8 * mm
    _right(c, w - 20 * mm, y, "Amount Payable: EUR 1.468,46", "Helvetica-Bold", 11)

    _text(c, 20 * mm, 20 * mm, "Payment within 30 days. IBAN on request.")
    c.save()


# --------------------------------------------------------------------------- #
# Invoice 3 — UK vendor: GBP, "April 2, 2024", "Invoice No.", tax INCLUDED
# --------------------------------------------------------------------------- #
def invoice_three(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4

    # Right-aligned company header — a visually different layout from the others.
    _right(c, w - 20 * mm, h - 22 * mm, "Crownsmith & Hart Ltd", "Helvetica-Bold", 16)
    _right(c, w - 20 * mm, h - 28 * mm, "44 Chancery Lane, London WC2A 1JX")
    _right(c, w - 20 * mm, h - 33 * mm, "accounts@crownsmithhart.example")

    _text(c, 20 * mm, h - 48 * mm, "INVOICE", "Helvetica-Bold", 18)
    _text(c, 20 * mm, h - 56 * mm, "Invoice No. CH-1042")
    _text(c, 20 * mm, h - 62 * mm, "Invoice Date: April 2, 2024")
    _text(c, 20 * mm, h - 68 * mm, "Due Date: May 2, 2024")

    _text(c, 20 * mm, h - 82 * mm, "Bill To:", "Helvetica-Bold")
    _text(c, 20 * mm, h - 88 * mm, "Pembroke Legal LLP")
    _text(c, 20 * mm, h - 93 * mm, "12 Gray's Inn Road, London WC1X 8HN")

    y = h - 114 * mm
    _text(c, 20 * mm, y, "Service", "Helvetica-Bold")
    _right(c, w - 20 * mm, y, "Amount", "Helvetica-Bold")
    c.line(20 * mm, y - 2 * mm, w - 20 * mm, y - 2 * mm)
    y -= 10 * mm
    _text(c, 20 * mm, y, "Brand identity & design retainer (Q2)")
    _right(c, w - 20 * mm, y, "GBP 3,600.00")
    y -= 14 * mm

    _right(c, w - 20 * mm, y, "Balance Due: GBP 3,600.00", "Helvetica-Bold", 11)
    y -= 10 * mm
    # Tax folded into the price — no itemised tax line on purpose.
    _text(c, 20 * mm, y, "Price includes VAT @ 20%.", "Helvetica-Oblique", 9)

    _text(c, 20 * mm, 20 * mm, "Payable by bank transfer.")
    c.save()


# --------------------------------------------------------------------------- #
# Invoice 4 — bare "INVOICE 0042" id, DD-MM-YYYY dash dates, USD
# --------------------------------------------------------------------------- #
def invoice_four(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=LETTER)
    w, h = LETTER

    _text(c, 25 * mm, h - 24 * mm, "Globex Industrial Supply", "Helvetica-Bold", 17)
    _text(c, 25 * mm, h - 30 * mm, "9 Foundry Road, Pittsburgh, PA 15201")

    _text(c, 25 * mm, h - 44 * mm, "INVOICE 0042", "Helvetica-Bold", 13)
    _text(c, 25 * mm, h - 51 * mm, "Invoice Date: 18-04-2024")
    _text(c, 25 * mm, h - 57 * mm, "Due Date: 18-05-2024")

    _text(c, 25 * mm, h - 71 * mm, "Bill To:", "Helvetica-Bold")
    _text(c, 25 * mm, h - 77 * mm, "Vantage Manufacturing Co.")
    _text(c, 25 * mm, h - 82 * mm, "300 Steel St, Cleveland, OH 44114")

    y = h - 102 * mm
    _text(c, 25 * mm, y, "Item", "Helvetica-Bold")
    _right(c, w - 25 * mm, y, "Line Total", "Helvetica-Bold")
    c.line(25 * mm, y - 2 * mm, w - 25 * mm, y - 2 * mm)
    y -= 10 * mm
    for desc, amt in [
        ("Hydraulic fittings (bulk)", "$3,120.00"),
        ("Stainless fasteners (case)", "$1,700.00"),
    ]:
        _text(c, 25 * mm, y, desc)
        _right(c, w - 25 * mm, y, amt)
        y -= 7 * mm

    y -= 6 * mm
    _right(c, w - 25 * mm, y, "Subtotal: $4,820.00")
    y -= 6 * mm
    _right(c, w - 25 * mm, y, "Tax (7%): $337.40")
    y -= 8 * mm
    _right(c, w - 25 * mm, y, "Amount Due: $5,157.40", "Helvetica-Bold", 11)

    c.save()


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    builders = [
        ("01_northwind_us_usd.pdf", invoice_one),
        ("02_zenith_eu_eur_no_duedate.pdf", invoice_two),
        ("03_crownsmith_uk_gbp_tax_included.pdf", invoice_three),
        ("04_globex_us_usd_dashed_dates.pdf", invoice_four),
    ]
    for filename, builder in builders:
        target = SAMPLES_DIR / filename
        builder(target)
        print(f"wrote {target.relative_to(SAMPLES_DIR.parent)}")
    print(f"\n{len(builders)} sample invoices written to {SAMPLES_DIR}")
    print("These are fictional demonstration documents - not real client data.")


if __name__ == "__main__":
    main()
