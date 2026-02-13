"""Unit tests for Phase 8: Heading Insertion with callout handling.

Tests multi-paragraph callout preservation including:
- Callout blocks continuing across empty lines
- End_text marker detection
- Heading breaks in callouts
- Different callout type transitions
- EOF handling for unclosed callouts
"""

import json

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase8 import Phase8
from gm_kit.pdf_convert.state import ConversionState


def _phase_status_ok(status: PhaseStatus) -> bool:
    """Check if phase status is ok (success or warning)."""
    return status in [PhaseStatus.SUCCESS, PhaseStatus.WARNING]


class TestMultiParagraphCalloutHandling:
    """Test multi-paragraph callout preservation in Phase 8."""

    def test__should_preserve_empty_lines_within_callout(self, tmp_path):
        """Empty lines within a callout should be blockquoted, not break the callout."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        # Create mapping with callout label
        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": "callout_gm"},
            ]
        }
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Create phase6 content with multi-paragraph callout
        # Note: Each line needs its own marker for Phase 8 to process correctly
        phase6_content = """«sig001:GM Note: First paragraph.»
«sig001:»
«sig001:Second paragraph after empty line.»
«sig001:»
«sig001:Third paragraph.»"""

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        # Create callout config with end_text to close the callout
        callout_config = [
            {"start_text": "GM Note:", "end_text": "Third paragraph.", "label": "callout_gm"}
        ]
        callout_config_path = output_dir / "callout_config.json"
        callout_config_path.write_text(json.dumps(callout_config))

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_callout_config_file": str(callout_config_path)},
        )

        result = phase.execute(state)

        # Phase should complete (may have warnings)
        assert _phase_status_ok(result.status)

        # Check phase8 output
        phase8_path = output_dir / "test-phase8.md"
        content = phase8_path.read_text()

        # All content lines should be blockquoted
        assert "> GM Note: First paragraph." in content
        assert "> " in content  # Empty line blockquoted
        assert "> Second paragraph after empty line." in content
        assert "> Third paragraph." in content

    def test__should_terminate_callout_on_end_text_marker(self, tmp_path):
        """Callout should end when end_text marker is found."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": "callout_gm"},
                {"id": "sig002", "family": "Body", "size": 10.0, "label": None},
            ]
        }
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Phase 6 content with end marker
        phase6_content = """«sig001:GM Note: This is secret info End of Note»
«sig002:Normal body text»"""

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        # Create callout config with end_text
        callout_config = [
            {"start_text": "GM Note:", "end_text": "End of Note", "label": "callout_gm"}
        ]
        callout_config_path = output_dir / "callout_config.json"
        callout_config_path.write_text(json.dumps(callout_config))

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_callout_config_file": str(callout_config_path)},
        )

        result = phase.execute(state)

        # Phase should complete (may have warnings)
        assert _phase_status_ok(result.status)

        phase8_path = output_dir / "test-phase8.md"
        content = phase8_path.read_text()

        # Callout line should be blockquoted
        assert "> GM Note: This is secret info End of Note" in content
        # Body text should NOT be blockquoted
        assert "Normal body text" in content
        assert "> Normal body text" not in content

    def test__should_terminate_callout_on_heading(self, tmp_path):
        """Callout should end when a heading is encountered."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": "callout_gm"},
                {"id": "sig002", "family": "Heading", "size": 16.0, "label": "H2"},
            ]
        }
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = """«sig001:GM Note: Secret info»
«sig002:Next Section»"""

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        callout_config_path = output_dir / "callout_config.json"
        callout_config_path.write_text("[]")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_callout_config_file": str(callout_config_path)},
        )

        result = phase.execute(state)

        # Phase should complete (may have warnings)
        assert _phase_status_ok(result.status)

        phase8_path = output_dir / "test-phase8.md"
        content = phase8_path.read_text()

        # Callout should be blockquoted
        assert "> GM Note: Secret info" in content
        # Heading should NOT be blockquoted
        assert "## Next Section" in content
        assert "> ## Next Section" not in content

    def test__should_switch_callout_type_on_different_label(self, tmp_path):
        """Switching from one callout type to another should end previous callout."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": "callout_gm"},
                {"id": "sig002", "family": "Body", "size": 10.0, "label": "callout_read_aloud"},
            ]
        }
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = """«sig001:GM Note: Secret»
«sig002:Read Aloud: You see a door»"""

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        callout_config_path = output_dir / "callout_config.json"
        callout_config_path.write_text("[]")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_callout_config_file": str(callout_config_path)},
        )

        result = phase.execute(state)

        # Phase should complete (may have warnings)
        assert _phase_status_ok(result.status)

        phase8_path = output_dir / "test-phase8.md"
        content = phase8_path.read_text()

        # Both should be blockquoted (different callout blocks)
        assert "> GM Note: Secret" in content
        assert "> Read Aloud: You see a door" in content

    def test__should_warn_on_unclosed_callout_at_eof(self, tmp_path):
        """Should warn when callout reaches EOF without explicit end_text marker."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": "callout_gm"},
            ]
        }
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Callout without end marker
        phase6_content = "«sig001:GM Note: Unclosed callout»"

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        # Config with end_text that won't be found
        callout_config = [
            {"start_text": "GM Note:", "end_text": "End of Note", "label": "callout_gm"}
        ]
        callout_config_path = output_dir / "callout_config.json"
        callout_config_path.write_text(json.dumps(callout_config))

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_callout_config_file": str(callout_config_path)},
        )

        result = phase.execute(state)

        # Phase should complete with warning status
        assert result.status == PhaseStatus.WARNING

        # Should have warning about unclosed callout
        step_82 = next((s for s in result.steps if s.step_id == "8.2"), None)
        assert step_82 is not None
        assert step_82.message is not None
        assert "not explicitly closed" in step_82.message

        # Should have warning in result
        assert len(result.warnings) > 0
        assert any("reached end of document" in w for w in result.warnings)

    def test__should_not_break_callout_on_page_marker(self, tmp_path):
        """Page markers should not break callout blocks."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": "callout_gm"},
            ]
        }
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Content with page marker inside callout
        phase6_content = """«sig001:GM Note: Start of note»
<!-- Page 2 -->
«sig001:Continue note»"""

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        callout_config_path = output_dir / "callout_config.json"
        callout_config_path.write_text("[]")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_callout_config_file": str(callout_config_path)},
        )

        result = phase.execute(state)

        # Phase should complete (may have warnings)
        assert _phase_status_ok(result.status)

        phase8_path = output_dir / "test-phase8.md"
        content = phase8_path.read_text()

        # Page marker should be blockquoted as part of callout
        assert "> <!-- Page 2 -->" in content


class TestPhase8EdgeCases:
    """Test edge cases for Phase 8."""

    def test__should_handle_missing_callout_config(self, tmp_path):
        """Phase 8 should work without callout config (uses defaults)."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": "callout_gm"},
            ]
        }
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:GM Note: Test»"

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        # No callout config in state
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        # Phase should complete (may have warnings)
        assert _phase_status_ok(result.status)

        phase8_path = output_dir / "test-phase8.md"
        content = phase8_path.read_text()

        assert "> GM Note: Test" in content

    def test__should_handle_invalid_callout_config(self, tmp_path):
        """Phase 8 should handle invalid callout config gracefully."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": "callout_gm"},
            ]
        }
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:GM Note: Test»"

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        # Invalid JSON in callout config
        callout_config_path = output_dir / "callout_config.json"
        callout_config_path.write_text("invalid json")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_callout_config_file": str(callout_config_path)},
        )

        result = phase.execute(state)

        # Should still succeed with warning
        assert _phase_status_ok(result.status)

    def test__should_handle_empty_phase6_content(self, tmp_path):
        """Phase 8 should handle empty phase6 content."""
        phase = Phase8()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {"signatures": []}
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = ""

        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        callout_config_path = output_dir / "callout_config.json"
        callout_config_path.write_text("[]")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_callout_config_file": str(callout_config_path)},
        )

        result = phase.execute(state)

        assert result.status == PhaseStatus.SUCCESS
