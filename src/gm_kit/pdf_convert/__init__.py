"""PDF to Markdown conversion orchestration module.

This module provides the PDF conversion pipeline orchestration,
including pre-flight analysis, state tracking, and phase execution.
"""

# Note: Imports are deferred to avoid circular imports
# Use explicit imports when needed:
#   from gm_kit.pdf_convert.state import ConversionState
#   from gm_kit.pdf_convert.metadata import PDFMetadata
#   from gm_kit.pdf_convert.preflight import PreflightReport
#   from gm_kit.pdf_convert.errors import ExitCode

__all__ = [
    "state",
    "metadata",
    "preflight",
    "errors",
    "phases",
]
