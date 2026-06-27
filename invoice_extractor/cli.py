"""Command-line interface for invoice_extractor.

Usage examples
--------------
    python -m invoice_extractor sample_invoices/ -o output/invoices.xlsx
    python -m invoice_extractor sample_invoices/ -o output/invoices.csv --format csv
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .extractor import extract_folder
from .output import write_csv, write_xlsx


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="invoice-extractor",
        description=(
            "Extract a folder of invoice PDFs (each with a different layout, "
            "currency, and date format) into one clean spreadsheet - one row per "
            "invoice. Anything ambiguous or missing is left blank and routed to a "
            "'Flagged for Review' list, never guessed."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python -m invoice_extractor sample_invoices/ -o output/invoices.xlsx\n"
            "  python -m invoice_extractor sample_invoices/ -o output/out.csv --format csv\n"
        ),
    )
    parser.add_argument(
        "input_folder",
        type=Path,
        help="folder containing the invoice PDFs to process",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/invoices.xlsx"),
        help="output file path (default: output/invoices.xlsx)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["xlsx", "csv"],
        default=None,
        help="output format; inferred from the output extension if omitted",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show per-file progress logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _resolve_format(args: argparse.Namespace) -> str:
    if args.format:
        return args.format
    suffix = args.output.suffix.lower()
    return "csv" if suffix == ".csv" else "xlsx"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )

    folder: Path = args.input_folder
    if not folder.is_dir():
        print(f"error: input folder not found: {folder}", file=sys.stderr)
        return 2

    result = extract_folder(folder)
    if result.invoice_count == 0:
        print(f"error: no PDF files found in {folder}", file=sys.stderr)
        return 1

    fmt = _resolve_format(args)
    if fmt == "csv":
        flagged_path = write_csv(result, args.output)
        extra = f"\n  flags:  {flagged_path}"
    else:
        write_xlsx(result, args.output)
        extra = ""

    # Concise, human-readable summary to stdout.
    flagged_invoices = {flag.source_file for flag in result.flags}
    print(
        f"Processed {result.invoice_count} invoice(s).\n"
        f"  {result.flag_count} item(s) flagged for review across "
        f"{len(flagged_invoices)} invoice(s).\n"
        f"  output: {args.output}{extra}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
