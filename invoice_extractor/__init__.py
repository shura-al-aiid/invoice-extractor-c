"""invoice_extractor — extract structured data from heterogeneous invoice PDFs.

The package turns a folder of invoice PDFs (each with a different layout,
currency, and date format) into one clean spreadsheet, one row per invoice.

Its guiding principle is conservative extraction: the tool never guesses. Any
value it cannot read with confidence is left blank in the main output and routed
to a "Flagged for Review" list with a reason, so a human makes the final call.
"""

__version__ = "1.0.0"

from .models import Flag, Invoice, ExtractionResult

__all__ = ["Flag", "Invoice", "ExtractionResult", "__version__"]
