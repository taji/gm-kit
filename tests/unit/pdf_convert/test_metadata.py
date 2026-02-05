"""Unit tests for PDF metadata extraction (T017)."""

import sys
from types import SimpleNamespace

import pytest

from gm_kit.pdf_convert.metadata import (
    PDFMetadata,
    extract_metadata,
    save_metadata,
    load_metadata,
    _safe_string,
    _parse_pdf_date,
)

class _FakePage:
    def __init__(self, images, fonts):
        self._images = images
        self._fonts = fonts

    def get_images(self):
        return self._images

    def get_fonts(self):
        return self._fonts


class _FakeDoc:
    def __init__(self, pages, metadata=None, toc=None, is_encrypted=False):
        self._pages = pages
        self.metadata = metadata or {}
        self._toc = toc or []
        self.is_encrypted = is_encrypted

    def __len__(self):
        return len(self._pages)

    def __iter__(self):
        return iter(self._pages)

    def get_toc(self):
        return self._toc

    def close(self):
        pass


@pytest.fixture
def fake_pdf(tmp_path, monkeypatch):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%Fake\n")

    pages = [
        _FakePage(
            images=[object(), object()],
            fonts=[
                (None, None, None, "Helvetica"),
                (None, None, None, "Times-Bold"),
            ],
        ),
        _FakePage(
            images=[object()],
            fonts=[(None, None, None, "Helvetica")],
        ),
    ]
    toc = [(1, "Chapter 1", 1), (2, "Section 1.1", 2)]
    metadata = {
        "title": "Test Title",
        "author": "Test Author",
        "creator": "Test Creator",
        "producer": "Test Producer",
        "creationDate": "D:20240115120000",
        "modDate": "20240116120000",
    }

    monkeypatch.setitem(
        sys.modules,
        "fitz",
        SimpleNamespace(open=lambda _p: _FakeDoc(pages, metadata=metadata, toc=toc)),
    )

    return pdf_path


class TestPDFMetadataDataclass:
    """Tests for PDFMetadata dataclass validation."""

    def test_pdf_metadata__should_create_valid_instance__when_valid_fields(self):
        """PDFMetadata accepts valid values."""
        metadata = PDFMetadata(
            page_count=10,
            file_size_bytes=1024,
            title="Test Title",
            author="Test Author",
            image_count=5,
            font_count=3,
        )
        assert metadata.page_count == 10
        assert metadata.file_size_bytes == 1024
        assert metadata.title == "Test Title"

    def test_pdf_metadata__should_reject__when_zero_page_count(self):
        """PDFMetadata rejects page_count <= 0."""
        with pytest.raises(ValueError, match="page_count must be > 0"):
            PDFMetadata(page_count=0, file_size_bytes=1024)

    def test_pdf_metadata__should_reject__when_negative_page_count(self):
        """PDFMetadata rejects negative page_count."""
        with pytest.raises(ValueError, match="page_count must be > 0"):
            PDFMetadata(page_count=-1, file_size_bytes=1024)

    def test_pdf_metadata__should_reject__when_zero_file_size(self):
        """PDFMetadata rejects file_size_bytes <= 0."""
        with pytest.raises(ValueError, match="file_size_bytes must be > 0"):
            PDFMetadata(page_count=10, file_size_bytes=0)

    def test_pdf_metadata__should_reject__when_negative_font_count(self):
        """PDFMetadata rejects negative font_count."""
        with pytest.raises(ValueError, match="font_count must be >= 0"):
            PDFMetadata(page_count=10, file_size_bytes=1024, font_count=-1)

    def test_pdf_metadata__should_reject__when_negative_image_count(self):
        """PDFMetadata rejects negative image_count."""
        with pytest.raises(ValueError, match="image_count must be >= 0"):
            PDFMetadata(page_count=10, file_size_bytes=1024, image_count=-1)

    def test_pdf_metadata__should_roundtrip__when_converted_to_dict_and_back(self):
        """PDFMetadata can roundtrip through dictionary."""
        original = PDFMetadata(
            page_count=10,
            file_size_bytes=1024,
            title="Test",
            author="Author",
            has_toc=True,
            toc_entries=5,
            toc_max_depth=3,
            image_count=10,
            font_count=4,
            copyright="(c) 2024",
            creation_date="2024-01-01T00:00:00",
        )
        data = original.to_dict()
        restored = PDFMetadata.from_dict(data)

        assert restored.page_count == original.page_count
        assert restored.file_size_bytes == original.file_size_bytes
        assert restored.title == original.title
        assert restored.has_toc == original.has_toc
        assert restored.toc_entries == original.toc_entries
        assert restored.copyright == original.copyright


class TestHelperFunctions:
    """Tests for metadata helper functions."""

    def test_safe_string__should_return_empty__when_none(self):
        """_safe_string returns empty string for None."""
        assert _safe_string(None) == ""

    def test_safe_string__should_pass_through__when_normal_string(self):
        """_safe_string passes through normal strings."""
        assert _safe_string("hello") == "hello"

    def test_safe_string__should_preserve__when_unicode_string(self):
        """_safe_string handles unicode correctly."""
        assert _safe_string("héllo wörld") == "héllo wörld"

    def test_safe_string__should_return_empty__when_str_raises(self):
        """_safe_string returns empty string when __str__ raises."""
        class _BadStr:
            def __str__(self):
                raise ValueError("boom")

        assert _safe_string(_BadStr()) == ""

    def test_parse_pdf_date__should_parse__when_prefix_present(self):
        """_parse_pdf_date handles D: prefixed dates."""
        result = _parse_pdf_date("D:20240115120000")
        assert result == "2024-01-15T12:00:00"

    def test_parse_pdf_date__should_parse__when_no_prefix(self):
        """_parse_pdf_date handles dates without prefix."""
        result = _parse_pdf_date("20240115120000")
        assert result == "2024-01-15T12:00:00"

    def test_parse_pdf_date__should_parse__when_date_only(self):
        """_parse_pdf_date handles date-only input."""
        result = _parse_pdf_date("D:20240115")
        assert result == "2024-01-15T00:00:00"

    def test_parse_pdf_date__should_return_none__when_empty_input(self):
        """_parse_pdf_date returns None for empty input."""
        assert _parse_pdf_date(None) is None
        assert _parse_pdf_date("") is None

    def test_parse_pdf_date__should_return_none__when_invalid_input(self):
        """_parse_pdf_date returns None for invalid input."""
        assert _parse_pdf_date("invalid") is None
        assert _parse_pdf_date("2024") is None
        assert _parse_pdf_date("D:20241301") is None


class TestExtractMetadata:
    """Tests for extract_metadata with mocked PDF."""

    def test_extract_metadata__should_extract_page_count__when_valid_pdf(self, fake_pdf):
        """extract_metadata returns correct page count."""
        metadata = extract_metadata(fake_pdf)
        assert metadata.page_count == 2

    def test_extract_metadata__should_extract_file_size__when_valid_pdf(self, fake_pdf):
        """extract_metadata returns correct file size."""
        metadata = extract_metadata(fake_pdf)
        expected_size = fake_pdf.stat().st_size
        assert metadata.file_size_bytes == expected_size

    def test_extract_metadata__should_extract_image_count__when_valid_pdf(self, fake_pdf):
        """extract_metadata counts images."""
        metadata = extract_metadata(fake_pdf)
        assert metadata.image_count == 3

    def test_extract_metadata__should_extract_font_count__when_valid_pdf(self, fake_pdf):
        """extract_metadata counts fonts."""
        metadata = extract_metadata(fake_pdf)
        assert metadata.font_count == 2

    def test_extract_metadata__should_extract_toc_info__when_valid_pdf(self, fake_pdf):
        """extract_metadata extracts TOC information."""
        metadata = extract_metadata(fake_pdf)
        assert metadata.has_toc is True
        assert metadata.toc_entries == 2
        assert metadata.toc_max_depth == 2

    def test_extract_metadata__should_set_extracted_at__when_valid_pdf(self, fake_pdf):
        """extract_metadata sets extracted_at timestamp."""
        metadata = extract_metadata(fake_pdf)
        assert metadata.extracted_at is not None
        # Should be ISO8601 format
        from datetime import datetime
        datetime.fromisoformat(metadata.extracted_at)


class TestExtractMetadataErrors:
    """Tests for extract_metadata error handling."""

    def test_extract_metadata__should_raise_file_not_found__when_nonexistent_file(self, tmp_path):
        """extract_metadata raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            extract_metadata(tmp_path / "nonexistent.pdf")

    def test_extract_metadata__should_raise_value_error__when_open_reports_encrypted(
        self,
        tmp_path,
        monkeypatch,
    ):
        """extract_metadata raises ValueError when fitz.open reports encryption."""
        pdf_path = tmp_path / "encrypted.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%Fake\n")

        def _open(_path):
            raise RuntimeError("File is encrypted and requires password")

        monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=_open))

        with pytest.raises(ValueError, match="PDF is encrypted or password-protected"):
            extract_metadata(pdf_path)

    def test_extract_metadata__should_raise_value_error__when_doc_is_encrypted(
        self,
        tmp_path,
        monkeypatch,
    ):
        """extract_metadata raises ValueError when doc.is_encrypted is true."""
        pdf_path = tmp_path / "encrypted.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%Fake\n")

        pages = [_FakePage(images=[], fonts=[])]
        monkeypatch.setitem(
            sys.modules,
            "fitz",
            SimpleNamespace(open=lambda _p: _FakeDoc(pages, is_encrypted=True)),
        )

        with pytest.raises(ValueError, match="PDF is encrypted or password-protected"):
            extract_metadata(pdf_path)

    def test_extract_metadata__should_reraise__when_open_fails_for_other_reasons(
        self,
        tmp_path,
        monkeypatch,
    ):
        """extract_metadata re-raises when fitz.open fails for other reasons."""
        pdf_path = tmp_path / "broken.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%Fake\n")

        def _open(_path):
            raise RuntimeError("unexpected failure")

        monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=_open))

        with pytest.raises(RuntimeError, match="unexpected failure"):
            extract_metadata(pdf_path)


class TestSaveAndLoadMetadata:
    """Tests for metadata persistence."""

    def test_save_load_metadata__should_roundtrip__when_valid_metadata(self, tmp_path):
        """Metadata can be saved and loaded."""
        original = PDFMetadata(
            page_count=10,
            file_size_bytes=1024,
            title="Test Document",
            has_toc=True,
            toc_entries=5,
        )

        path = save_metadata(original, tmp_path)
        assert path.exists()
        assert path.name == "metadata.json"

        loaded = load_metadata(tmp_path)
        assert loaded is not None
        assert loaded.page_count == original.page_count
        assert loaded.title == original.title
        assert loaded.has_toc == original.has_toc

    def test_load_metadata__should_return_none__when_file_missing(self, tmp_path):
        """load_metadata returns None when file doesn't exist."""
        result = load_metadata(tmp_path)
        assert result is None

    def test_save_metadata__should_create_directory__when_path_not_exists(self, tmp_path):
        """save_metadata creates directory if needed."""
        nested_dir = tmp_path / "nested" / "path"
        metadata = PDFMetadata(page_count=1, file_size_bytes=100)

        path = save_metadata(metadata, nested_dir)
        assert path.exists()
