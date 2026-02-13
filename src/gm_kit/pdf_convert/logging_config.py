"""Logging configuration for PDF conversion pipeline.

Provides UTF-8 encoded logging with ASCII box formatting for phases and steps.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, TextIO


class TeeOutput:
    """Tee output to both original stream and log file.

    Captures stdout/stderr and writes to both console and log file.
    """

    def __init__(self, original: TextIO, log_path: Path) -> None:
        self.original = original
        self.log_path = log_path
        self.encoding = "utf-8"

    def write(self, data: str) -> int:
        """Write to both original stream and log file."""
        # Write to original stream
        result = self.original.write(data)
        self.original.flush()

        # Also write to log file
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(data)
        except OSError:
            # If log file can't be written, continue with console only
            pass

        return result

    def flush(self) -> None:
        """Flush the original stream."""
        self.original.flush()

    def __getattr__(self, name: str) -> Any:
        """Delegate other attributes to original stream."""
        return getattr(self.original, name)


class ConversionLogFormatter(logging.Formatter):
    """Formatter for standard log messages in conversion log.

    Formats regular log messages (not phase/step structure) in a clean way.
    """

    def __init__(self) -> None:
        super().__init__(fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def setup_conversion_logging(output_dir: Path) -> logging.Logger:
    """Configure logging for PDF conversion pipeline.

    Sets up:
    - File handler writing to {output_dir}/conversion.log with UTF-8 encoding
    - Console handler for stdout/stderr
    - TeeOutput to capture print statements to log file

    Args:
        output_dir: Directory where conversion.log will be written

    Returns:
        Configured logger instance
    """
    log_path = output_dir / "conversion.log"

    # Create or clear log file
    log_path.write_text("", encoding="utf-8")

    # Get the conversion logger
    logger = logging.getLogger("gm_kit.pdf_convert")
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    logger.handlers = []

    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(ConversionLogFormatter())
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ConversionLogFormatter())
    logger.addHandler(console_handler)

    # Capture stdout/stderr to log file
    sys.stdout = TeeOutput(sys.stdout, log_path)
    sys.stderr = TeeOutput(sys.stderr, log_path)

    logger.info("Conversion logging initialized")

    return logger


def reset_output_streams() -> None:
    """Reset stdout/stderr to original streams.

    Should be called at end of conversion to restore normal output.
    """
    if isinstance(sys.stdout, TeeOutput):
        sys.stdout = sys.stdout.original
    if isinstance(sys.stderr, TeeOutput):
        sys.stderr = sys.stderr.original
