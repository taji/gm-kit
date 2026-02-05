"""Error handling for PDF conversion pipeline.

Defines exit codes and error message constants per FR-029 through FR-048a.
"""

from enum import IntEnum

from gm_kit.pdf_convert.constants import PHASE_MAX, PHASE_MIN


class ExitCode(IntEnum):
    """CLI exit codes per FR-044 through FR-048a.

    Attributes:
        SUCCESS: Successful completion (0)
        USER_ABORT: User cancelled operation (1)
        FILE_ERROR: File/path errors - not found, permissions (2)
        PDF_ERROR: PDF processing errors - scanned, extraction failure (3)
        STATE_ERROR: State/resume errors - corrupt state, missing phase input (4)
        DEPENDENCY_ERROR: Dependency errors - missing required modules (5)
    """
    SUCCESS = 0
    USER_ABORT = 1
    FILE_ERROR = 2
    PDF_ERROR = 3
    STATE_ERROR = 4
    DEPENDENCY_ERROR = 5


# Error message templates per FR-029 through FR-041
# Format: (prefix, message, suggestion)

class ErrorMessages:
    """Error message constants per FR-029 through FR-041.

    Each message follows the actionable format per FR-041b:
    - Error type prefix (ERROR/WARNING/ABORT)
    - Brief description of what failed
    - Suggested action or next step
    """

    # FR-029: Missing/unreadable PDF
    PDF_NOT_FOUND = (
        "ERROR",
        "Cannot open PDF - file not found or corrupted",
        "Check the file path and ensure the file exists",
    )

    # FR-030: Scanned PDF
    SCANNED_PDF = (
        "ERROR",
        "Scanned PDF detected - very little extractable text",
        "Use external OCR tool first, then retry",
    )

    # FR-031: User cancelled
    USER_CANCELLED = (
        "ABORT",
        "User cancelled after pre-flight report",
        None,
    )

    # FR-032: Cannot create output directory
    OUTPUT_DIR_ERROR = (
        "ERROR",
        "Cannot create output directory - check permissions",
        "Verify you have write access to the parent directory",
    )

    # FR-033: Failed to create text-only PDF
    TEXT_PDF_ERROR = (
        "ERROR",
        "Failed to create text-only PDF",
        "Check disk space and PDF integrity",
    )

    # FR-034: No TOC found
    NO_TOC = (
        "WARNING",
        "No TOC found - hierarchy may be incomplete",
        None,
    )

    # FR-035: No text extracted
    NO_TEXT = (
        "ERROR",
        "No text extracted from PDF",
        "PDF may be image-only; use OCR first",
    )

    # FR-036: Two-column issues
    TWO_COLUMN = (
        "WARNING",
        "Pervasive two-column issues detected - expect manual review",
        None,
    )

    # FR-037: Phase input missing
    PHASE_INPUT_MISSING = (
        "ERROR",
        "Phase input file not found - run previous phase first",
        "Use --from-step to re-run from an earlier step",
    )

    # FR-038: Font mapping invalid
    FONT_MAPPING_ERROR = (
        "ERROR",
        "font-family-mapping.json not found or malformed",
        "Re-run Phase 3 to regenerate font mapping",
    )

    # FR-039: No heading sources
    NO_HEADINGS = (
        "WARNING",
        "No heading sources available - flat document structure",
        None,
    )

    # FR-040: Many lint violations
    MANY_VIOLATIONS = (
        "WARNING",
        "Many lint violations - document may need significant cleanup",
        None,
    )

    # FR-041: Bundle creation failed
    BUNDLE_FAILED = (
        "WARNING",
        "Failed to create zip bundle - files saved individually",
        None,
    )

    # Permission denied on PDF read
    PDF_PERMISSION = (
        "ERROR",
        "Cannot read PDF - permission denied",
        "Check file permissions and try again",
    )

    # Encrypted PDF
    PDF_ENCRYPTED = (
        "ERROR",
        "PDF is encrypted or password-protected. Please provide an unprotected PDF",
        None,
    )

    # State file missing for resume
    STATE_MISSING = (
        "ERROR",
        "Cannot resume - state file missing or corrupt",
        "Use 'gmkit pdf-convert <pdf-path>' to start fresh",
    )

    # State file corrupt
    STATE_CORRUPT = (
        "ERROR",
        "State file is corrupted",
        "Delete .state.json and restart conversion",
    )

    # State version mismatch
    STATE_VERSION = (
        "ERROR",
        "State file version requires newer gmkit version",
        "Please upgrade gmkit to continue",
    )

    # Disk full
    DISK_FULL = (
        "ERROR",
        "Disk full - cannot write output file. Free up space and resume",
        "Use: gmkit pdf-convert --resume <dir>",
    )

    # Lock contention
    LOCK_CONTENTION = (
        "ERROR",
        "Another conversion is in progress in this directory",
        "Wait for it to complete or use a different output directory",
    )

    # Missing output file on resume
    OUTPUT_MISSING = (
        "ERROR",
        "Phase output file missing",
        "Re-run the phase with: gmkit pdf-convert --phase N <dir>",
    )

    # Dependency error (e.g., PyMuPDF)
    DEPENDENCY_MISSING = (
        "ERROR",
        "Installation appears corrupted - missing required module",
        "Reinstall with: uv pip install gmkit",
    )

    # Invalid --phase value
    INVALID_PHASE = (
        "ERROR",
        f"--phase requires an integer between {PHASE_MIN} and {PHASE_MAX}",
        None,
    )

    # Invalid --from-step format
    INVALID_STEP = (
        "ERROR",
        "--from-step requires format N.N (e.g., 5.3)",
        None,
    )

    # Mutually exclusive flags
    EXCLUSIVE_FLAGS = (
        "ERROR",
        "Cannot combine --resume, --phase, --from-step, or --status",
        "Use only one operation mode",
    )


def format_error(
    error: tuple,
    context: str | None = None,
) -> str:
    """Format an error message for display.

    Args:
        error: Error tuple (prefix, message, suggestion)
        context: Optional additional context (file path, phase number, etc.)

    Returns:
        Formatted error message string
    """
    prefix, message, suggestion = error

    parts = [f"{prefix}: {message}"]

    if context:
        parts[0] = f"{prefix}: {message} ({context})"

    if suggestion:
        parts.append(f"  {suggestion}")

    return "\n".join(parts)


def get_exit_code_for_error(error: tuple) -> ExitCode:
    """Get the appropriate exit code for an error message.

    Args:
        error: Error tuple from ErrorMessages

    Returns:
        Appropriate ExitCode
    """
    prefix = error[0]

    if prefix == "ABORT":
        return ExitCode.USER_ABORT

    # Determine based on message content
    message = error[1].lower()

    if any(word in message for word in ["permission", "not found", "cannot open"]):
        return ExitCode.FILE_ERROR

    if any(word in message for word in ["pdf", "scanned", "extracted", "encrypted"]):
        return ExitCode.PDF_ERROR

    if any(word in message for word in ["state", "resume", "phase input", "output"]):
        return ExitCode.STATE_ERROR

    if "installation" in message or "module" in message:
        return ExitCode.DEPENDENCY_ERROR

    # Default to FILE_ERROR for unmatched errors
    return ExitCode.FILE_ERROR
