"""Regenerate the README before/after preview image (docs/preview.png).

Run after generating samples:

    python scripts/generate_samples.py
    python scripts/make_preview.py

The image is rendered from the *actual* extraction result, so the "after" table
always reflects what the tool really produces — it is never a mock-up.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Allow running as a plain script (python scripts/make_preview.py) by ensuring the
# repo root — which contains the invoice_extractor package — is importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from invoice_extractor.extractor import extract_folder  # noqa: E402
SAMPLES = ROOT / "sample_invoices"
OUT = ROOT / "docs" / "preview.png"

# Palette
BG = (247, 248, 250)
INK = (33, 37, 41)
MUTED = (108, 117, 125)
HEADER = (31, 78, 120)
WHITE = (255, 255, 255)
LINE = (222, 226, 230)
FLAG = (192, 57, 43)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a common sans-serif font, falling back to PIL's default."""
    candidates = (
        ["arialbd.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    result = extract_folder(SAMPLES)

    W, H = 1180, 560
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    f_title = _font(26, bold=True)
    f_h = _font(17, bold=True)
    f = _font(15)
    f_small = _font(13)

    d.text((40, 24), "invoice-extractor", font=f_title, fill=INK)
    d.text(
        (40, 60),
        "A folder of mismatched invoice PDFs  →  one clean, analysis-ready spreadsheet",
        font=f,
        fill=MUTED,
    )

    # ---------------- BEFORE panel ----------------
    bx, by = 40, 110
    d.text((bx, by), "BEFORE", font=f_h, fill=MUTED)
    descriptions = [
        ("01  Northwind (US)", "USD $ · 03/14/2024 · 'Invoice #'"),
        ("02  Zenith (DE)", "EUR € · '5 March 2024' · 1.234,00 · no due date"),
        ("03  Crownsmith (UK)", "GBP £ · 'April 2, 2024' · VAT in total"),
        ("04  Globex (US)", "USD $ · 18-04-2024 · 'INVOICE 0042'"),
    ]
    cy = by + 34
    for title, sub in descriptions:
        d.rounded_rectangle((bx, cy, bx + 360, cy + 64), radius=8, fill=WHITE, outline=LINE)
        d.text((bx + 14, cy + 12), title, font=f_h, fill=INK)
        d.text((bx + 14, cy + 36), sub, font=f_small, fill=MUTED)
        cy += 78

    # Arrow between the two panels, vertically centred on the table.
    ax = bx + 396
    d.text((ax, 205), "→", font=_font(46, bold=True), fill=HEADER)

    # ---------------- AFTER panel ----------------
    tx, ty = 470, 110
    d.text((tx, ty), "AFTER  —  Extracted Invoices", font=f_h, fill=MUTED)

    headers = ["File", "Vendor", "Date", "Curr", "Subtotal", "Tax", "Total"]
    widths = [70, 150, 92, 50, 90, 80, 90]
    table_x, table_y = tx, ty + 30
    row_h = 30

    # Header row
    cx = table_x
    d.rectangle((table_x, table_y, table_x + sum(widths), table_y + row_h), fill=HEADER)
    for head, wdt in zip(headers, widths):
        d.text((cx + 8, table_y + 8), head, font=f_small, fill=WHITE)
        cx += wdt

    # Data rows
    def money(v):
        return f"{v:,.2f}" if v is not None else "—"

    ry = table_y + row_h
    for inv in result.invoices:
        cells = [
            inv.source_file.split("_")[0],
            (inv.vendor or "")[:18],
            inv.invoice_date or "—",
            inv.currency or "—",
            money(inv.subtotal),
            money(inv.tax),
            money(inv.total),
        ]
        cx = table_x
        d.rectangle(
            (table_x, ry, table_x + sum(widths), ry + row_h),
            fill=WHITE,
            outline=LINE,
        )
        for i, (cell, wdt) in enumerate(zip(cells, widths)):
            colour = MUTED if cell == "—" else INK
            d.text((cx + 8, ry + 8), str(cell), font=f_small, fill=colour)
            cx += wdt
        ry += row_h

    # Flag callout
    fy = ry + 22
    d.text((tx, fy), "Flagged for Review (not guessed)", font=f_h, fill=FLAG)
    flag_lines = [f"• {fl.source_file.split('_')[0]}: {fl.issue}" for fl in result.flags]
    for i, line in enumerate(flag_lines[:4]):
        d.text((tx, fy + 26 + i * 22), line[:74], font=f_small, fill=INK)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}  ({W}x{H})")


if __name__ == "__main__":
    main()
