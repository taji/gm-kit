"""PDF metadata extraction module.

Extracts metadata from PDF files using PyMuPDF (fitz).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class PDFMetadata:
    """Extracted PDF properties.

    Persisted in `metadata.json` in the output directory.

    Attributes:
        title: PDF title from metadata (empty string if not present)
        author: Author name from metadata (empty string if not present)
        creator: Creating application (empty string if not present)
        producer: PDF producer (empty string if not present)
        copyright: Copyright notice if found (None if not present)
        page_count: Total pages in the PDF
        file_size_bytes: File size in bytes
        has_toc: Whether embedded TOC (outline) exists
        toc_entries: Number of TOC entries (0 if none)
        toc_max_depth: Maximum nesting level of TOC (0 if none)
        image_count: Total images across all pages
        font_count: Unique font families detected
        extracted_at: When metadata was extracted (ISO8601)
        creation_date: PDF creation date (ISO8601 or None)
        modification_date: PDF modification date (ISO8601 or None)
    """
    page_count: int
    file_size_bytes: int
    title: str = ""
    author: str = ""
    creator: str = ""
    producer: str = ""
    copyright: Optional[str] = None
    has_toc: bool = False
    toc_entries: int = 0
    toc_max_depth: int = 0
    image_count: int = 0
    font_count: int = 0
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate required fields."""
        if self.page_count <= 0:
            raise ValueError(f"page_count must be > 0, got {self.page_count}")
        if self.file_size_bytes <= 0:
            raise ValueError(f"file_size_bytes must be > 0, got {self.file_size_bytes}")
        if self.font_count < 0:
            raise ValueError(f"font_count must be >= 0, got {self.font_count}")
        if self.image_count < 0:
            raise ValueError(f"image_count must be >= 0, got {self.image_count}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PDFMetadata:
        """Create PDFMetadata from dictionary."""
        return cls(
            page_count=data["page_count"],
            file_size_bytes=data["file_size_bytes"],
            title=data.get("title", ""),
            author=data.get("author", ""),
            creator=data.get("creator", ""),
            producer=data.get("producer", ""),
            copyright=data.get("copyright"),
            has_toc=data.get("has_toc", False),
            toc_entries=data.get("toc_entries", 0),
            toc_max_depth=data.get("toc_max_depth", 0),
            image_count=data.get("image_count", 0),
            font_count=data.get("font_count", 0),
            extracted_at=data.get("extracted_at", datetime.now().isoformat()),
            creation_date=data.get("creation_date"),
            modification_date=data.get("modification_date"),
        )


def _safe_string(value: Any) -> str:
    """Convert value to string, handling None and encoding issues.

    Invalid characters are replaced with Unicode replacement character (U+FFFD).
    """
    if value is None:
        return ""
    try:
        result = str(value)
        # Replace any invalid characters
        return result.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return ""


def _parse_pdf_date(date_str: Optional[str]) -> Optional[str]:
    """Parse PDF date format to ISO8601.

    PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'
    Returns None if date cannot be parsed.
    """
    if not date_str:
        return None

    try:
        # Remove D: prefix if present
        if date_str.startswith("D:"):
            date_str = date_str[2:]

        # Basic parsing - extract YYYYMMDD at minimum
        if len(date_str) >= 8:
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])

            hour = int(date_str[8:10]) if len(date_str) >= 10 else 0
            minute = int(date_str[10:12]) if len(date_str) >= 12 else 0
            second = int(date_str[12:14]) if len(date_str) >= 14 else 0

            dt = datetime(year, month, day, hour, minute, second)
            return dt.isoformat()
    except (ValueError, IndexError):
        pass

    return None


def extract_metadata(pdf_path: Path) -> PDFMetadata:
    """Extract metadata from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        PDFMetadata with extracted information

    Raises:
        FileNotFoundError: If PDF file does not exist
        PermissionError: If PDF file cannot be read
        ValueError: If PDF is encrypted or invalid
    """
    import fitz  # type: ignore[import-untyped]  # PyMuPDF

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    file_size = pdf_path.stat().st_size

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        if "encrypted" in str(e).lower() or "password" in str(e).lower():
            raise ValueError("PDF is encrypted or password-protected")
        raise

    try:
        # Check if encrypted
        if doc.is_encrypted:
            raise ValueError("PDF is encrypted or password-protected")

        # Get basic metadata
        metadata = doc.metadata or {}

        # Count pages
        page_count = len(doc)

        # Get TOC (outline)
        toc = doc.get_toc()
        has_toc = len(toc) > 0
        toc_entries = len(toc)
        toc_max_depth = max((entry[0] for entry in toc), default=0) if toc else 0

        # Count images across all pages
        image_count = 0
        for page in doc:
            image_count += len(page.get_images())

        # Count unique font families
        font_names = set()
        for page in doc:
            fonts = page.get_fonts()
            for font in fonts:
                # font[3] is the font name
                if font[3]:
                    # Extract base font name (before any +, -, or space)
                    base_name = font[3].split("+")[-1].split("-")[0].split(" ")[0]
                    font_names.add(base_name.lower())
        font_count = len(font_names)

        return PDFMetadata(
            page_count=page_count,
            file_size_bytes=file_size,
            title=_safe_string(metadata.get("title")),
            author=_safe_string(metadata.get("author")),
            creator=_safe_string(metadata.get("creator")),
            producer=_safe_string(metadata.get("producer")),
            copyright=metadata.get("copyright") or None,
            has_toc=has_toc,
            toc_entries=toc_entries,
            toc_max_depth=toc_max_depth,
            image_count=image_count,
            font_count=font_count,
            creation_date=_parse_pdf_date(metadata.get("creationDate")),
            modification_date=_parse_pdf_date(metadata.get("modDate")),
        )
    finally:
        doc.close()


def save_metadata(metadata: PDFMetadata, output_dir: Path) -> Path:
    """Save metadata to metadata.json in the output directory.

    Args:
        metadata: PDFMetadata to save
        output_dir: Directory to save to

    Returns:
        Path to the saved metadata file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata.to_dict(), f, indent=2)

    return metadata_path


def load_metadata(output_dir: Path) -> Optional[PDFMetadata]:
    """Load metadata from metadata.json in the output directory.

    Args:
        output_dir: Directory containing metadata.json

    Returns:
        PDFMetadata if file exists, None otherwise
    """
    metadata_path = Path(output_dir) / "metadata.json"

    if not metadata_path.exists():
        return None

    with open(metadata_path) as f:
        data = json.load(f)

    return PDFMetadata.from_dict(data)
