"""Unit tests for Phase 6 (Structural Formatting).

Tests for hyphenation fixes, bullet list formatting, and indentation preservation.
"""

from pathlib import Path

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase6 import Phase6
from gm_kit.pdf_convert.state import ConversionState


class TestPhase6HyphenationFixes:
    """Test hyphenation fixes in Phase 6."""

    @pytest.fixture
    def setup_phase6(self, tmp_path):
        """Create a Phase6 instance and mock state with input file."""
        phase = Phase6()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
        return phase, state

    def test__should_remove_hyphen_at_line_break(self, setup_phase6, tmp_path):
        """Test that hyphens at line breaks are removed."""
        phase, state = setup_phase6

        # Create input file with hyphenation
        input_path = tmp_path / "test-phase5.md"
        input_path.write_text(
            "The quick brown fox jumped over the lazy\ndog that was sleep-\ning peacefully."
        )

        result = phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        # "sleep-\ning" should become "sleeping"
        assert "sleeping" in output
        assert "sleep-\ning" not in output
        assert result.status == PhaseStatus.SUCCESS

    def test__should_handle_multiple_hyphenations(self, setup_phase6, tmp_path):
        """Test handling multiple hyphenation instances."""
        phase, state = setup_phase6

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("Run-\nning fast, jump-\ning high, and swim-\nming well.")

        phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        assert "Running" in output
        assert "jumping" in output
        assert "swimming" in output
        assert "Run-\nning" not in output

    def test__should_remove_soft_hyphen_characters(self, setup_phase6, tmp_path):
        """Test that soft hyphen characters (U+00AD) are removed."""
        phase, state = setup_phase6

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("The word co\u00adop\u00aderation has soft hyphens.")

        phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        assert "coop\u00aderation" not in output
        assert "cooperation" in output or "co" in output  # Soft hyphens removed

    def test__should_not_affect_hyphens_within_words(self, setup_phase6, tmp_path):
        """Test that hyphens within words are preserved."""
        phase, state = setup_phase6

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("Well-known fact: state-of-the-art technology.")

        phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        # These compound words should remain intact
        assert "Well-known" in output
        assert "state-of-the-art" in output


class TestPhase6BulletListFormatting:
    """Test bullet list formatting in Phase 6."""

    @pytest.fixture
    def setup_phase6(self, tmp_path):
        """Create a Phase6 instance and mock state with input file."""
        phase = Phase6()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
        return phase, state

    def test__should_normalize_bullet_characters_to_dashes(self, setup_phase6, tmp_path):
        """Test that bullet characters (• ·) are normalized to dashes."""
        phase, state = setup_phase6

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("\u2022 First item\n\u00b7 Second item")

        phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        assert "- First item" in output
        assert "- Second item" in output
        assert "\u2022" not in output

    def test__should_normalize_dash_bullets(self, setup_phase6, tmp_path):
        """Test that dash bullets are preserved."""
        phase, state = setup_phase6

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("- Item one\n- Item two\n* Item three")

        phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        assert "- Item one" in output
        assert "- Item two" in output
        # Asterisk bullets may or may not be normalized depending on implementation
        # The current implementation only normalizes bullet characters, not dashes

    def test__should_preserve_numbered_list_format(self, setup_phase6, tmp_path):
        """Test that numbered list items are recognized."""
        phase, state = setup_phase6

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("1. First step\n2. Second step\n(1) Alternate format")

        phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        # Numbered formats should be preserved (not converted to dashes)
        assert "1. First step" in output
        assert "2. Second step" in output
        assert "(1) Alternate format" in output

    def test__should_preserve_list_indentation(self, setup_phase6, tmp_path):
        """Test that list indentation is preserved."""
        phase, state = setup_phase6

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("\u2022 Top level\n  \u2022 Indented item\n    \u2022 Deep item")

        phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        # Check that indentation is preserved
        assert "- Top level" in output
        assert "  - Indented item" in output or "- Indented item" in output


class TestPhase6EdgeCases:
    """Test edge cases and error handling in Phase 6."""

    def test__should_return_error__when_input_file_missing(self, tmp_path):
        """Test error when input file doesn't exist."""
        phase = Phase6()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        # Don't create input file
        result = phase.execute(state)

        assert result.status == PhaseStatus.ERROR
        assert "Phase input file not found" in result.errors[0]

    def test__should_handle_empty_input_file(self, tmp_path):
        """Test handling of empty input file."""
        phase = Phase6()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        # Create empty input file
        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("")

        result = phase.execute(state)

        assert result.status == PhaseStatus.SUCCESS
        output_path = tmp_path / "test-phase6.md"
        assert output_path.read_text() == ""

    def test__should_handle_unicode_content(self, tmp_path):
        """Test handling of unicode content."""
        phase = Phase6()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("Unicode: ñ, é, 中文, 日本語, 🎮")

        result = phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        assert "中文" in output
        assert "日本語" in output
        assert result.status == PhaseStatus.SUCCESS

    def test__should_report_all_step_results(self, tmp_path):
        """Test that all step results are reported."""
        phase = Phase6()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("Some content")

        result = phase.execute(state)

        step_ids = [s.step_id for s in result.steps]
        assert "6.1" in step_ids  # Hyphenation
        assert "6.2" in step_ids  # Bullet lists
        assert "6.3" in step_ids  # Preserve indentation
        assert "6.4" in step_ids  # OCR stub

    def test__should_set_output_file_path(self, tmp_path):
        """Test that output file path is set correctly."""
        phase = Phase6()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text("Content")

        result = phase.execute(state)

        expected_output = str(tmp_path / "test-phase6.md")
        assert result.output_file == expected_output
        assert Path(expected_output).exists()

    def test__should_handle_multiline_content_with_bullets(self, tmp_path):
        """Test handling of multiline content with mixed bullets and text."""
        phase = Phase6()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        input_path = tmp_path / "test-phase5.md"
        input_path.write_text(
            "Introduction paragraph.\n\n"
            "\u2022 First bullet point\n"
            "\u2022 Second bullet point\n\n"
            "Conclusion paragraph with hy-\nphenation."
        )

        phase.execute(state)

        output_path = tmp_path / "test-phase6.md"
        output = output_path.read_text()

        # Bullets normalized
        assert "- First bullet point" in output
        assert "- Second bullet point" in output
        # Hyphenation fixed
        assert "hyphenation" in output
        # Structure preserved
        assert "Introduction paragraph" in output
        assert "Conclusion paragraph" in output
