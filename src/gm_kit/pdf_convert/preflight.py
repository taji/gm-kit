"""Pre-flight analysis module for PDF conversion.

Analyzes PDF files before conversion and displays results to user.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from gm_kit.pdf_convert.metadata import PDFMetadata, extract_metadata

logger = logging.getLogger(__name__)


class TOCApproach(str, Enum):
    """How to handle table of contents."""
    EMBEDDED = "embedded"  # PDF has embedded outline
    VISUAL = "visual"      # Need agent to parse visual TOC page
    NONE = "none"          # No TOC detected


class Complexity(str, Enum):
    """Complexity rating for PDF conversion."""
    LOW = "low"           # Simple PDF, minimal user review needed
    MODERATE = "moderate" # Average complexity
    HIGH = "high"         # Complex layout, expect more user involvement


@dataclass
class PreflightReport:
    """Analysis results shown to user before conversion.

    Not persisted (derived from PDFMetadata).

    Attributes:
        pdf_name: Filename for display
        file_size_display: Human-readable size (e.g., "12.4 MB")
        page_count: Total pages
        image_count: Total images
        text_extractable: True if >100 chars extracted
        toc_approach: How TOC will be handled
        font_complexity: Complexity based on font count
        overall_complexity: Overall conversion complexity
        warnings: Any pre-flight warnings
        user_involvement_phases: Phases requiring user input
        copyright_notice: Copyright from metadata if found
    """
    pdf_name: str
    file_size_display: str
    page_count: int
    image_count: int
    text_extractable: bool
    toc_approach: TOCApproach
    font_complexity: Complexity
    overall_complexity: Complexity
    warnings: List[str] = field(default_factory=list)
    user_involvement_phases: List[int] = field(default_factory=lambda: [7, 9])
    copyright_notice: Optional[str] = None


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != 'B' else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _calculate_font_complexity(font_count: int) -> Complexity:
    """Calculate font complexity based on font count.

    Per FR-015:
    - Low: ≤3 unique font families
    - Moderate: 4-8 unique font families
    - High: >8 unique font families
    """
    if font_count <= 3:
        return Complexity.LOW
    elif font_count <= 8:
        return Complexity.MODERATE
    else:
        return Complexity.HIGH


def _calculate_overall_complexity(
    font_complexity: Complexity,
    page_count: int,
    image_count: int,
    has_tables: bool = False,
    has_multi_column: bool = False,
) -> Complexity:
    """Calculate overall conversion complexity.

    Per FR-015:
    - Low: ≤3 fonts, ≤10 images, no detected tables
    - Moderate: 4-8 fonts, 11-50 images, or detected tables
    - High: >8 fonts, >50 images, multi-column layout, or math notation
    """
    # Start with font complexity as baseline
    if font_complexity == Complexity.HIGH:
        return Complexity.HIGH

    # Check image count
    if image_count > 50:
        return Complexity.HIGH
    elif image_count > 10:
        if font_complexity == Complexity.MODERATE:
            return Complexity.HIGH
        return Complexity.MODERATE

    # Check for complex layouts
    if has_multi_column:
        return Complexity.HIGH

    if has_tables:
        return Complexity.MODERATE if font_complexity == Complexity.LOW else Complexity.HIGH

    return font_complexity


def _determine_toc_approach(metadata: PDFMetadata) -> TOCApproach:
    """Determine how to handle table of contents."""
    if metadata.has_toc and metadata.toc_entries > 0:
        return TOCApproach.EMBEDDED
    # For now, assume visual TOC detection would happen in agent phase
    # We could add heuristics here later
    return TOCApproach.NONE


def check_text_extractability(pdf_path: Path, threshold: int = 100) -> bool:
    """Check if PDF has extractable text.

    Args:
        pdf_path: Path to PDF file
        threshold: Minimum characters required (default 100 per FR-014)

    Returns:
        True if PDF has sufficient extractable text
    """
    import fitz

    try:
        doc = fitz.open(str(pdf_path))
        total_chars = 0

        # Check first few pages (or all if small document)
        pages_to_check = min(5, len(doc))
        for i in range(pages_to_check):
            page = doc[i]
            text = page.get_text()
            total_chars += len(text.strip())
            if total_chars >= threshold:
                doc.close()
                return True

        doc.close()
        return total_chars >= threshold
    except Exception:
        return False


def analyze_pdf(pdf_path: Path) -> PreflightReport:
    """Perform pre-flight analysis on a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        PreflightReport with analysis results
    """
    pdf_path = Path(pdf_path)

    # Extract metadata
    metadata = extract_metadata(pdf_path)

    # Check text extractability
    text_extractable = check_text_extractability(pdf_path)

    # Calculate complexities
    font_complexity = _calculate_font_complexity(metadata.font_count)
    overall_complexity = _calculate_overall_complexity(
        font_complexity=font_complexity,
        page_count=metadata.page_count,
        image_count=metadata.image_count,
    )

    # Determine TOC approach
    toc_approach = _determine_toc_approach(metadata)

    # Build warnings
    warnings = []
    if not text_extractable:
        warnings.append("Scanned PDF detected - very little extractable text")
    if metadata.file_size_bytes > 50 * 1024 * 1024:  # 50MB
        warnings.append("Very large file - may require extended processing")
    if overall_complexity == Complexity.HIGH:
        warnings.append("Complex document - expect more user involvement")
    if toc_approach == TOCApproach.NONE:
        warnings.append("No TOC found - hierarchy may be incomplete")

    return PreflightReport(
        pdf_name=pdf_path.name,
        file_size_display=_format_file_size(metadata.file_size_bytes),
        page_count=metadata.page_count,
        image_count=metadata.image_count,
        text_extractable=text_extractable,
        toc_approach=toc_approach,
        font_complexity=font_complexity,
        overall_complexity=overall_complexity,
        warnings=warnings,
        copyright_notice=metadata.copyright,
    )


def display_preflight_report(
    report: PreflightReport,
    console: Optional[Console] = None,
) -> None:
    """Display pre-flight report to user.

    Formats output per FR-016a specification.

    Args:
        report: PreflightReport to display
        console: Rich console to use (creates new if None)
    """
    if console is None:
        console = Console()

    # Header
    console.print("=" * 62)
    console.print("  Pre-flight Analysis Complete", style="bold")
    console.print("=" * 62)
    console.print()

    # PDF info
    console.print(f"PDF: {report.pdf_name} ({report.file_size_display}, {report.page_count} pages)")
    console.print()

    # Metrics table
    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Metric", width=20)
    table.add_column("Value", width=20)
    table.add_column("Note", width=30)

    # Images
    table.add_row(
        "Images",
        str(report.image_count),
        "Will be extracted to images/" if report.image_count > 0 else ""
    )

    # Text
    table.add_row(
        "Text",
        "extractable" if report.text_extractable else "none",
        "Native text found" if report.text_extractable else "Scanned PDF"
    )

    # TOC
    toc_note = {
        TOCApproach.EMBEDDED: "Will use PDF outline",
        TOCApproach.VISUAL: "Parse visual TOC",
        TOCApproach.NONE: "",
    }
    table.add_row(
        "TOC",
        report.toc_approach.value,
        toc_note[report.toc_approach]
    )

    # Fonts
    table.add_row(
        "Fonts",
        f"{report.font_complexity.value} complexity",
        ""
    )

    # Copyright
    copyright_display = f'"{report.copyright_notice}"' if report.copyright_notice else "Not found"
    table.add_row(
        "Copyright",
        copyright_display[:40],
        "Found in metadata" if report.copyright_notice else ""
    )

    # Overall complexity
    table.add_row(
        "Complexity",
        report.overall_complexity.value,
        ""
    )

    console.print(table)
    console.print()

    # Warnings
    for warning in report.warnings:
        console.print(f"[yellow]WARNING:[/yellow] {warning}")

    if report.warnings:
        console.print()

    # User involvement notice
    phases_str = ", ".join(str(p) for p in report.user_involvement_phases)
    console.print(f"User involvement required in: Phase {phases_str}")
    console.print()


def prompt_user_confirmation(
    console: Optional[Console] = None,
    auto_proceed: bool = False,
) -> bool:
    """Prompt user to proceed with conversion.

    Args:
        console: Rich console to use
        auto_proceed: If True, skip prompt and return True (--yes flag)

    Returns:
        True if user wants to proceed, False to abort
    """
    if auto_proceed:
        return True

    if console is None:
        console = Console()

    console.print("Options:")
    console.print("  A) Proceed with conversion")
    console.print("  B) Abort")
    console.print()

    while True:
        try:
            choice = input("Your choice [A/B]: ").strip().upper()
            if choice in ('A', 'PROCEED', 'YES', 'Y'):
                return True
            elif choice in ('B', 'ABORT', 'NO', 'N'):
                return False
            else:
                console.print("Please enter A or B")
        except (EOFError, KeyboardInterrupt):
            return False


def run_preflight(
    pdf_path: Path,
    console: Optional[Console] = None,
    auto_proceed: bool = False,
) -> Optional[PreflightReport]:
    """Run complete pre-flight analysis and display results.

    Args:
        pdf_path: Path to PDF file
        console: Rich console for output
        auto_proceed: Skip confirmation prompt if True

    Returns:
        PreflightReport if user proceeds, None if aborted
    """
    report = analyze_pdf(pdf_path)
    display_preflight_report(report, console)

    if not report.text_extractable:
        if console is None:
            console = Console()
        console.print(
            "[red]ERROR:[/red] Scanned PDF detected - very little extractable text",
            file=sys.stderr
        )
        console.print("Recommendation: Use external OCR tool first.", file=sys.stderr)
        return None

    if prompt_user_confirmation(console, auto_proceed):
        return report
    else:
        return None
