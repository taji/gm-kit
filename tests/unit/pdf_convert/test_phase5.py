"""Unit tests for Phase 5 backtick-wrapping of markdown-sensitive characters."""

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase5 import _wrap_inner_content, _wrap_md_sensitive_chars
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
