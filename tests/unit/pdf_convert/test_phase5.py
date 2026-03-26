"""Unit tests for Phase 5 backtick-wrapping of markdown-sensitive characters."""

import json

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase5 import Phase5, _wrap_inner_content, _wrap_md_sensitive_chars
from gm_kit.pdf_convert.state import ConversionState


class TestWrapInnerContent:
    """Test pure string wrapping of markdown-sensitive elements."""

    def test__should_wrap_html_open_tag(self):
        result = _wrap_inner_content("Use <span> for")
        assert result == "Use `<span>` for"

    def test__should_wrap_html_close_tag(self):
        result = _wrap_inner_content("end </span> here")
        assert result == "end `</span>` here"

    def test__should_wrap_self_closing_tag(self):
        result = _wrap_inner_content("break <br/> here")
        assert result == "break `<br/>` here"

    def test__should_wrap_tag_with_attributes(self):
        result = _wrap_inner_content('a <div class="x"> b')
        assert result == 'a `<div class="x">` b'

    def test__should_wrap_double_curly_braces(self):
        result = _wrap_inner_content("use {{ class }}")
        assert result == "use `{{ class }}`"

    def test__should_wrap_single_curly_braces(self):
        result = _wrap_inner_content("open { and }")
        assert result == "open `{` and `}`"

    def test__should_wrap_pipe(self):
        result = _wrap_inner_content(r"col1 \| col2")
        assert result == r"col1 `\|` col2"

    def test__should_wrap_backslash_word(self):
        result = _wrap_inner_content(r"use \page cmd")
        assert result == r"use `\page` cmd"

    def test__should_not_wrap_escaped_guillemets(self):
        result = _wrap_inner_content(r"text \« here")
        assert result == r"text \« here"

    def test__should_wrap_standalone_colon(self):
        result = _wrap_inner_content(": list item")
        assert result == "`:` list item"

    def test__should_not_wrap_colon_after_word(self):
        result = _wrap_inner_content("Strength: 18")
        assert result == "Strength: 18"

    def test__should_not_double_wrap(self):
        result = _wrap_inner_content("already `<span>` here")
        assert result == "already `<span>` here"

    def test__should_handle_multiple_elements(self):
        result = _wrap_inner_content("<span> and </span>")
        assert result == "`<span>` and `</span>`"

    def test__should_not_modify_plain_text(self):
        result = _wrap_inner_content("Hello world")
        assert result == "Hello world"


class TestWrapMdSensitiveChars:
    """Test wrapping across marked/unmarked text with metadata preservation."""

    def test__should_wrap_marked_and_unmarked_text(self):
        content = "<b>outside</b> «sig001:<b>inside</b>»"
        result = _wrap_md_sensitive_chars(content)
        assert result == "`<b>`outside`</b>` «sig001:`<b>`inside`</b>`»"

    def test__should_preserve_marker_delimiters(self):
        result = _wrap_md_sensitive_chars("«sig001:<div>»")
        assert "«sig001:" in result
        assert result.endswith("»")
        assert "`<div>`" in result

    def test__should_handle_empty_marker(self):
        # Empty marker has no content to match [^»]+, so regex won't match
        content = "«sig001:»"
        result = _wrap_md_sensitive_chars(content)
        assert result == "«sig001:»"

    def test__should_preserve_page_marker_html_comments(self):
        content = "<b>outside</b>\n<!-- Page 2 -->\n«sig001:<i>inside</i>»"
        result = _wrap_md_sensitive_chars(content)
        assert "<!-- Page 2 -->" in result
        assert "`<b>`outside`</b>`" in result
        assert "«sig001:`<i>`inside`</i>`»" in result


class TestNormalizeLineBreaks:
    """Test step 5.2 line merging with marker-wrapped content."""

    @pytest.fixture
    def run_phase5(self, tmp_path):
        """Run Phase5 on given input content and return output content."""
        from gm_kit.pdf_convert.phases.phase5 import Phase5

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")

        def _run(input_text):
            input_path = output_dir / "test-phase4.md"
            input_path.write_text(input_text, encoding="utf-8")

            state = ConversionState(pdf_path=str(pdf_path), output_dir=str(output_dir))
            phase = Phase5()
            result = phase.execute(state)
            assert result.status == PhaseStatus.SUCCESS

            output_path = output_dir / "test-phase5.md"
            return output_path.read_text(encoding="utf-8")

        return _run

    def test__should_not_merge_marker_lines(self, run_phase5):
        """Two consecutive marker-wrapped lines must stay separate."""
        input_text = "«sig001:First paragraph.»\n«sig002:Second paragraph.»\n"
        output = run_phase5(input_text)
        lines = [line for line in output.split("\n") if line.strip()]
        assert len(lines) == 2
        assert "First paragraph." in lines[0]
        assert "Second paragraph." in lines[1]

    def test__should_still_merge_plain_text_continuations(self, run_phase5):
        """Non-marker plain text lines should still merge as before."""
        input_text = "This is the start\nof a paragraph.\n"
        output = run_phase5(input_text)
        lines = [line for line in output.split("\n") if line.strip()]
        assert len(lines) == 1
        assert "This is the start of a paragraph." in lines[0]

    def test__should_preserve_blank_line_paragraph_breaks(self, run_phase5):
        """Blank lines between paragraphs are preserved."""
        input_text = "«sig001:First paragraph.»\n\n«sig001:Second paragraph.»\n"
        output = run_phase5(input_text)
        assert "\n\n" in output
        non_empty = [line for line in output.split("\n") if line.strip()]
        assert len(non_empty) == 2


class TestFooterWatermarkConfidenceFiltering:
    """Regression tests for low-confidence footer signature filtering (phase5 step 5.1.4).

    Root cause: sig012 (Unnamed-T3, 9pt) was used as both print-instruction labels
    AND as table column headers in the Homebrewery fixture. Phase 3 correctly flagged
    it as a footer with confidence='low' (mixed position). Phase 5 was removing it
    anyway, wiping table headers Head A/B/C from the output.
    Fix: _detect_footer_watermarks_from_config now skips low-confidence footer sigs.
    """

    def _make_footer_config(self, tmp_path, footer_signatures):
        cfg = {
            "watermark_signatures": [],
            "page_number_signatures": [],
            "footer_signatures": footer_signatures,
        }
        path = tmp_path / "footer_config.json"
        path.write_text(json.dumps(cfg), encoding="utf-8")
        return path

    def test__should_skip_low_confidence_footer_sig__when_confidence_is_low(self, tmp_path):
        """Low-confidence footer signatures must NOT be added to the removal set."""
        self._make_footer_config(
            tmp_path,
            [
                {
                    "sig_id": "sig012",
                    "sample": "Destination",
                    "position": "mixed",
                    "confidence": "low",
                }
            ],
        )
        phase = Phase5()
        result = phase._detect_footer_watermarks_from_config(tmp_path)
        assert "sig012" not in result

    def test__should_include_medium_confidence_footer_sig__when_confidence_is_medium(
        self, tmp_path
    ):
        """Medium-confidence footer signatures should be included."""
        self._make_footer_config(
            tmp_path,
            [{"sig_id": "sig015", "sample": "PART", "position": "bottom", "confidence": "medium"}],
        )
        phase = Phase5()
        result = phase._detect_footer_watermarks_from_config(tmp_path)
        assert "sig015" in result

    def test__should_include_high_confidence_footer_sig__when_confidence_is_high(self, tmp_path):
        """High-confidence footer signatures should be included."""
        self._make_footer_config(
            tmp_path,
            [
                {
                    "sig_id": "sig009",
                    "sample": "footer text",
                    "position": "bottom",
                    "confidence": "high",
                }
            ],
        )
        phase = Phase5()
        result = phase._detect_footer_watermarks_from_config(tmp_path)
        assert "sig009" in result

    def test__should_default_to_include__when_confidence_field_missing(self, tmp_path):
        """A footer sig with no confidence field should be included (safe default)."""
        self._make_footer_config(
            tmp_path,
            [{"sig_id": "sig020", "sample": "no confidence"}],
        )
        phase = Phase5()
        result = phase._detect_footer_watermarks_from_config(tmp_path)
        assert "sig020" in result

    def test__should_always_include_watermark_sigs__regardless_of_category(self, tmp_path):
        """Watermark signatures (always high) must never be filtered out."""
        cfg = {
            "watermark_signatures": [{"sig_id": "sig013", "sample": "→", "confidence": "high"}],
            "page_number_signatures": [],
            "footer_signatures": [],
        }
        (tmp_path / "footer_config.json").write_text(json.dumps(cfg), encoding="utf-8")
        phase = Phase5()
        result = phase._detect_footer_watermarks_from_config(tmp_path)
        assert "sig013" in result

    def test__should_preserve_table_headers__when_sig_is_low_confidence_footer(self, tmp_path):
        """End-to-end: table header markers survive phase 5 when sig is low-confidence.

        Reproduces the Homebrewery regression: sig012 was removed by step 5.1.4 because
        it was flagged as a low-confidence footer, wiping 'Head A', 'Head B', 'Head C'.
        """
        self._make_footer_config(
            tmp_path,
            [
                {
                    "sig_id": "sig012",
                    "sample": "Destination",
                    "position": "mixed",
                    "confidence": "low",
                }
            ],
        )
        # Also write a minimal font-family-mapping.json so phase5 doesn't fail on load
        fmapping = {
            "version": "1.0",
            "signatures": [
                {
                    "id": "sig012",
                    "family": "Unnamed-T3",
                    "size": 9.0,
                    "weight": "normal",
                    "style": "normal",
                    "label": None,
                    "candidate_heading": False,
                    "samples": ["Destination"],
                },
            ],
        }
        (tmp_path / "font-family-mapping.json").write_text(json.dumps(fmapping), encoding="utf-8")

        content = "«sig012:Head A»\n«sig012:Head B»\n«sig012:Head C»\n«sig012:1A»\n«sig012:2A»\n"
        # Phase5 derives filenames from the PDF stem: dummy-phase4.md → dummy-phase5.md
        (tmp_path / "dummy-phase4.md").write_text(content, encoding="utf-8")

        state = ConversionState(
            pdf_path=str(tmp_path / "dummy.pdf"),
            output_dir=str(tmp_path),
        )

        phase = Phase5()
        phase.execute(state)

        phase5_output = tmp_path / "dummy-phase5.md"
        assert phase5_output.exists(), "phase5 output file not created"
        output_text = phase5_output.read_text(encoding="utf-8")

        assert "Head A" in output_text, "Table header 'Head A' was incorrectly removed"
        assert "Head B" in output_text, "Table header 'Head B' was incorrectly removed"
        assert "Head C" in output_text, "Table header 'Head C' was incorrectly removed"
