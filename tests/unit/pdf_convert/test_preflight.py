"""Unit tests for preflight analysis (T018)."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from gm_kit.pdf_convert.preflight import (
    PreflightReport,
    TOCApproach,
    Complexity,
    _format_file_size,
    _calculate_font_complexity,
    _calculate_overall_complexity,
    _determine_toc_approach,
    analyze_pdf,
    check_text_extractability,
    display_preflight_report,
    prompt_user_confirmation,
    run_preflight,
)
from gm_kit.pdf_convert.metadata import PDFMetadata


def _build_metadata(**overrides):
    data = {
        "page_count": 10,
        "file_size_bytes": 1024 * 1024,
        "has_toc": True,
        "toc_entries": 12,
        "toc_max_depth": 2,
        "image_count": 5,
        "font_count": 3,
    }
    data.update(overrides)
    return PDFMetadata(**data)


class _FakeDoc:
    def __init__(self, pages):
        self._pages = pages

    def __len__(self):
        return len(self._pages)

    def __getitem__(self, index):
        return self._pages[index]

    def close(self):
        pass


def _raise_open(_path):
    raise FileNotFoundError("missing")


@pytest.fixture
def fake_pdf_path(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test content")
    return pdf_path


@pytest.fixture
def stub_preflight(monkeypatch):
    def _apply(**overrides):
        metadata = _build_metadata(**overrides)
        monkeypatch.setattr(
            "gm_kit.pdf_convert.preflight.extract_metadata",
            lambda _pdf_path: metadata,
        )
        monkeypatch.setattr(
            "gm_kit.pdf_convert.preflight.check_text_extractability",
            lambda *_args, **_kwargs: True,
        )
        return metadata

    return _apply


class TestFormatFileSize:
    """Tests for _format_file_size helper."""

    def test_format_file_size__should_return_bytes__when_under_1kb(self):
        """Formats bytes correctly."""
        assert _format_file_size(500) == "500 B"

    def test_format_file_size__should_return_kilobytes__when_1kb_or_more(self):
        """Formats kilobytes correctly."""
        assert _format_file_size(1024) == "1.0 KB"
        assert _format_file_size(2048) == "2.0 KB"

    def test_format_file_size__should_return_megabytes__when_1mb_or_more(self):
        """Formats megabytes correctly."""
        assert _format_file_size(1024 * 1024) == "1.0 MB"
        assert _format_file_size(5 * 1024 * 1024) == "5.0 MB"

    def test_format_file_size__should_return_gigabytes__when_1gb_or_more(self):
        """Formats gigabytes correctly."""
        assert _format_file_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_format_file_size__should_return_terabytes__when_1tb_or_more(self):
        """Formats terabytes correctly."""
        assert _format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"


class TestCalculateFontComplexity:
    """Tests for font complexity calculation per FR-015."""

    def test_font_complexity__should_return_low__when_three_or_fewer_fonts(self):
        """Low complexity for <= 3 fonts."""
        assert _calculate_font_complexity(0) == Complexity.LOW
        assert _calculate_font_complexity(1) == Complexity.LOW
        assert _calculate_font_complexity(2) == Complexity.LOW
        assert _calculate_font_complexity(3) == Complexity.LOW

    def test_font_complexity__should_return_moderate__when_four_to_eight_fonts(self):
        """Moderate complexity for 4-8 fonts."""
        assert _calculate_font_complexity(4) == Complexity.MODERATE
        assert _calculate_font_complexity(5) == Complexity.MODERATE
        assert _calculate_font_complexity(8) == Complexity.MODERATE

    def test_font_complexity__should_return_high__when_more_than_eight_fonts(self):
        """High complexity for > 8 fonts."""
        assert _calculate_font_complexity(9) == Complexity.HIGH
        assert _calculate_font_complexity(20) == Complexity.HIGH


class TestCalculateOverallComplexity:
    """Tests for overall complexity calculation per FR-015."""

    def test_overall_complexity__should_return_low__when_simple_document(self):
        """Low complexity for simple document."""
        result = _calculate_overall_complexity(
            font_complexity=Complexity.LOW,
            page_count=10,
            image_count=5,
        )
        assert result == Complexity.LOW

    def test_overall_complexity__should_return_moderate__when_11_to_50_images(self):
        """Moderate complexity for 11-50 images."""
        result = _calculate_overall_complexity(
            font_complexity=Complexity.LOW,
            page_count=10,
            image_count=20,
        )
        assert result == Complexity.MODERATE

    def test_overall_complexity__should_return_high__when_more_than_50_images(self):
        """High complexity for > 50 images."""
        result = _calculate_overall_complexity(
            font_complexity=Complexity.LOW,
            page_count=10,
            image_count=51,
        )
        assert result == Complexity.HIGH

    def test_overall_complexity__should_return_high__when_font_complexity_is_high(self):
        """High font complexity propagates to overall."""
        result = _calculate_overall_complexity(
            font_complexity=Complexity.HIGH,
            page_count=10,
            image_count=5,
        )
        assert result == Complexity.HIGH

    def test_overall_complexity__should_return_high__when_moderate_fonts_and_moderate_images(self):
        """Moderate fonts + moderate images = high."""
        result = _calculate_overall_complexity(
            font_complexity=Complexity.MODERATE,
            page_count=10,
            image_count=20,  # 11-50 images
        )
        assert result == Complexity.HIGH

    def test_overall_complexity__should_increase__when_tables_detected(self):
        """Detected tables increase complexity."""
        result = _calculate_overall_complexity(
            font_complexity=Complexity.LOW,
            page_count=10,
            image_count=5,
            has_tables=True,
        )
        assert result == Complexity.MODERATE

    def test_overall_complexity__should_return_high__when_multi_column_layout(self):
        """Multi-column layout is high complexity."""
        result = _calculate_overall_complexity(
            font_complexity=Complexity.LOW,
            page_count=10,
            image_count=5,
            has_multi_column=True,
        )
        assert result == Complexity.HIGH


class TestDetermineTOCApproach:
    """Tests for TOC approach determination."""

    def test_toc_approach__should_return_embedded__when_toc_present(self):
        """Embedded TOC returns EMBEDDED approach."""
        metadata = PDFMetadata(
            page_count=10,
            file_size_bytes=1024,
            has_toc=True,
            toc_entries=10,
        )
        result = _determine_toc_approach(metadata)
        assert result == TOCApproach.EMBEDDED

    def test_toc_approach__should_return_none__when_no_toc(self):
        """No TOC returns NONE approach."""
        metadata = PDFMetadata(
            page_count=10,
            file_size_bytes=1024,
            has_toc=False,
            toc_entries=0,
        )
        result = _determine_toc_approach(metadata)
        assert result == TOCApproach.NONE

    def test_toc_approach__should_return_none__when_toc_flag_true_but_zero_entries(self):
        """has_toc True but zero entries returns NONE."""
        metadata = PDFMetadata(
            page_count=10,
            file_size_bytes=1024,
            has_toc=True,
            toc_entries=0,
        )
        result = _determine_toc_approach(metadata)
        assert result == TOCApproach.NONE


class TestPreflightReport:
    """Tests for PreflightReport dataclass."""

    def test_preflight_report__should_default_phases_to_7_and_9__when_constructed(self):
        """Default user involvement phases are 7 and 9."""
        report = PreflightReport(
            pdf_name="test.pdf",
            file_size_display="1.0 MB",
            page_count=10,
            image_count=5,
            text_extractable=True,
            toc_approach=TOCApproach.NONE,
            font_complexity=Complexity.LOW,
            overall_complexity=Complexity.LOW,
        )
        assert report.user_involvement_phases == [7, 9]

    def test_preflight_report__should_default_warnings_to_empty__when_constructed(self):
        """Warnings default to empty list."""
        report = PreflightReport(
            pdf_name="test.pdf",
            file_size_display="1.0 MB",
            page_count=10,
            image_count=5,
            text_extractable=True,
            toc_approach=TOCApproach.NONE,
            font_complexity=Complexity.LOW,
            overall_complexity=Complexity.LOW,
        )
        assert report.warnings == []


class TestAnalyzePdf:
    """Tests for analyze_pdf with actual PDF."""

    def test_analyze_pdf__should_return_preflight_report__when_called(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """analyze_pdf returns PreflightReport."""
        stub_preflight()
        report = analyze_pdf(fake_pdf_path)
        assert isinstance(report, PreflightReport)

    def test_analyze_pdf__should_include_pdf_name__when_called(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """Report includes PDF filename."""
        stub_preflight()
        report = analyze_pdf(fake_pdf_path)
        assert report.pdf_name == fake_pdf_path.name

    def test_analyze_pdf__should_include_formatted_file_size__when_called(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """Report includes formatted file size."""
        stub_preflight()
        report = analyze_pdf(fake_pdf_path)
        assert report.file_size_display is not None
        # Should be in format like "1.1 MB"
        assert any(unit in report.file_size_display for unit in ["B", "KB", "MB", "GB"])

    def test_analyze_pdf__should_include_page_count__when_called(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """Report includes page count."""
        stub_preflight()
        report = analyze_pdf(fake_pdf_path)
        assert report.page_count > 0

    def test_analyze_pdf__should_include_complexity_ratings__when_called(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """Report includes complexity ratings."""
        stub_preflight()
        report = analyze_pdf(fake_pdf_path)
        assert report.font_complexity in [Complexity.LOW, Complexity.MODERATE, Complexity.HIGH]
        assert report.overall_complexity in [Complexity.LOW, Complexity.MODERATE, Complexity.HIGH]

    def test_analyze_pdf__should_report_embedded_toc__when_outline_present(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """Report includes embedded TOC approach for the fixture PDF."""
        stub_preflight()
        report = analyze_pdf(fake_pdf_path)
        assert report.toc_approach == TOCApproach.EMBEDDED


class TestCheckTextExtractability:
    """Tests for text extractability check."""

    def test_check_text_extractability__should_return_true__when_pdf_has_text(
        self,
        monkeypatch,
        fake_pdf_path,
    ):
        """check_text_extractability returns True for PDF with text."""
        pages = [SimpleNamespace(get_text=lambda: "x" * 120)]
        monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=lambda _p: _FakeDoc(pages)))
        result = check_text_extractability(fake_pdf_path)
        # Assuming test PDF has extractable text
        assert result is True

    def test_check_text_extractability__should_return_false__when_threshold_very_high(
        self,
        monkeypatch,
        fake_pdf_path,
    ):
        """check_text_extractability respects threshold parameter."""
        pages = [SimpleNamespace(get_text=lambda: "x" * 50)]
        monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=lambda _p: _FakeDoc(pages)))
        # Very high threshold should return False
        result = check_text_extractability(fake_pdf_path, threshold=10000000)
        assert result is False

    def test_check_text_extractability__should_return_false__when_path_invalid(
        self,
        tmp_path,
        monkeypatch,
    ):
        """check_text_extractability returns False for invalid file."""
        monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=_raise_open))
        result = check_text_extractability(tmp_path / "nonexistent.pdf")
        assert result is False


class TestAnalyzePdfWarnings:
    """Tests for warning generation in analyze_pdf."""

    def test_analyze_pdf__should_warn__when_no_toc_found(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """Warning generated when no TOC found."""
        stub_preflight(
            has_toc=False,
            toc_entries=0,
            image_count=0,
            font_count=1,
        )
        report = analyze_pdf(fake_pdf_path)
        assert report.toc_approach == TOCApproach.NONE
        assert report.warnings == ["No TOC found - hierarchy may be incomplete"]

    def test_analyze_pdf__should_warn__when_high_complexity(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """Warning generated for high complexity documents."""
        stub_preflight(image_count=51)
        report = analyze_pdf(fake_pdf_path)
        assert report.overall_complexity == Complexity.HIGH
        assert report.warnings == ["Complex document - expect more user involvement"]

    def test_analyze_pdf__should_warn__when_text_not_extractable(
        self,
        stub_preflight,
        fake_pdf_path,
        monkeypatch,
    ):
        """Warning generated when text is not extractable."""
        stub_preflight(has_toc=True, toc_entries=1, image_count=0, font_count=1)
        monkeypatch.setattr(
            "gm_kit.pdf_convert.preflight.check_text_extractability",
            lambda *_args, **_kwargs: False,
        )
        report = analyze_pdf(fake_pdf_path)
        assert report.warnings == ["Scanned PDF detected - very little extractable text"]

    def test_analyze_pdf__should_warn__when_file_size_large(
        self,
        stub_preflight,
        fake_pdf_path,
    ):
        """Warning generated when file exceeds 50MB."""
        stub_preflight(
            file_size_bytes=51 * 1024 * 1024,
            has_toc=True,
            toc_entries=1,
            image_count=0,
            font_count=1,
        )
        report = analyze_pdf(fake_pdf_path)
        assert report.warnings == ["Very large file - may require extended processing"]


class TestDisplayPreflightReport:
    """Tests for display_preflight_report output."""

    def test_display_report__should_include_warning_and_user_phases__when_called(self):
        """Preflight report output includes warnings and involvement phases."""
        report = PreflightReport(
            pdf_name="test.pdf",
            file_size_display="1.0 MB",
            page_count=10,
            image_count=2,
            text_extractable=True,
            toc_approach=TOCApproach.NONE,
            font_complexity=Complexity.LOW,
            overall_complexity=Complexity.LOW,
            warnings=["No TOC found - hierarchy may be incomplete"],
        )
        from rich.console import Console

        console = Console(record=True)
        display_preflight_report(report, console=console)

        output = console.export_text()
        assert "Pre-flight Analysis Complete" in output
        assert "WARNING:" in output
        assert "User involvement required in: Phase 7, 9" in output


class TestPromptUserConfirmation:
    """Tests for prompt_user_confirmation."""

    def test_prompt_user_confirmation__should_return_true__when_auto_proceed(self):
        """auto_proceed skips prompt and returns True."""
        assert prompt_user_confirmation(auto_proceed=True) is True

    def test_prompt_user_confirmation__should_return_true__when_valid_choice_entered(
        self,
        monkeypatch,
    ):
        """Valid choice returns True after invalid input."""
        inputs = iter(["x", "A"])
        monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
        from rich.console import Console

        console = Console(record=True)
        assert prompt_user_confirmation(console=console) is True


class TestRunPreflight:
    """Tests for run_preflight."""

    def test_run_preflight__should_return_none__when_scanned_pdf_detected(self, monkeypatch):
        """Scanned PDFs return None with warning output."""
        report = PreflightReport(
            pdf_name="test.pdf",
            file_size_display="1.0 MB",
            page_count=10,
            image_count=0,
            text_extractable=False,
            toc_approach=TOCApproach.NONE,
            font_complexity=Complexity.LOW,
            overall_complexity=Complexity.LOW,
        )
        monkeypatch.setattr("gm_kit.pdf_convert.preflight.analyze_pdf", lambda _p: report)
        monkeypatch.setattr(
            "gm_kit.pdf_convert.preflight.display_preflight_report",
            lambda *_args, **_kwargs: None,
        )
        assert run_preflight(Path("test.pdf")) is None

    def test_run_preflight__should_return_report__when_user_proceeds(self, monkeypatch):
        """Returns report when user confirms."""
        report = PreflightReport(
            pdf_name="test.pdf",
            file_size_display="1.0 MB",
            page_count=10,
            image_count=0,
            text_extractable=True,
            toc_approach=TOCApproach.NONE,
            font_complexity=Complexity.LOW,
            overall_complexity=Complexity.LOW,
        )
        monkeypatch.setattr("gm_kit.pdf_convert.preflight.analyze_pdf", lambda _p: report)
        monkeypatch.setattr(
            "gm_kit.pdf_convert.preflight.display_preflight_report",
            lambda *_args, **_kwargs: None,
        )
        monkeypatch.setattr(
            "gm_kit.pdf_convert.preflight.prompt_user_confirmation",
            lambda *_args, **_kwargs: True,
        )
        assert run_preflight(Path("test.pdf")) is report
