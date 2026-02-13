import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase5 import Phase5
from gm_kit.pdf_convert.state import ConversionState


# Define a fixture for a mock ConversionState
@pytest.fixture
def mock_state(tmp_path):
    state = MagicMock(spec=ConversionState)
    state.output_dir = str(tmp_path)
    state.pdf_path = str(tmp_path / "test.pdf")
    return state


@pytest.fixture
def phase5_instance():
    return Phase5()


class TestPhase5MarkerRemoval:  # Renamed class
    def test_remove_icon_markers_success(self, mock_state, phase5_instance):
        output_dir = Path(mock_state.output_dir)
        pdf_name = Path(mock_state.pdf_path).stem

        # Create mock font-family-mapping.json with FontAwesome signatures
        font_mapping_data = {
            "signatures": [
                {
                    "id": "sig010",
                    "family": "FontAwesome6Free-Solid",
                    "size": 9.6,
                    "weight": "normal",
                    "style": "normal",
                },
                {
                    "id": "sig017",
                    "family": "FontAwesome6Free-Regular",
                    "size": 9.0,
                    "weight": "normal",
                    "style": "normal",
                },
                {
                    "id": "sig009",
                    "family": "Unnamed-T3",
                    "size": 9.6,
                    "weight": "normal",
                    "style": "normal",
                },
            ]
        }
        (output_dir / "font-family-mapping.json").write_text(json.dumps(font_mapping_data))

        # Create mock icon_config.json with FontAwesome signatures
        icon_config = {
            "icon_signatures": [
                {"sig_id": "sig010", "font_family": "FontAwesome6Free-Solid", "confidence": "high"},
                {
                    "sig_id": "sig017",
                    "font_family": "FontAwesome6Free-Regular",
                    "confidence": "high",
                },
            ]
        }
        (output_dir / "icon_config.json").write_text(json.dumps(icon_config))

        # Create mock phase4.md input with icon markers
        input_content = """\
Line 1: Some text «sig010:» with an icon.
Line 2: Another icon «sig017:» here.
Line 3: Mixed text «sig009: text» and other stuff.
Line 4: Only an icon on this line «sig010:A».
Line 5: Multiple icons «sig010:1» «sig017:2» in a row.
"""
        (output_dir / f"{pdf_name}-phase4.md").write_text(input_content)

        # Execute Phase5
        result = phase5_instance.execute(mock_state)

        # Assertions
        assert result.status == PhaseStatus.SUCCESS
        assert (output_dir / f"{pdf_name}-phase5.md").exists()

        output_content = (output_dir / f"{pdf_name}-phase5.md").read_text()

        # Icon markers should be removed
        assert "«sig010:»" not in output_content
        assert "«sig017:»" not in output_content
        assert "«sig010:A»" not in output_content
        assert "«sig010:1»" not in output_content
        assert "«sig017:2»" not in output_content

        # Non-icon markers should remain
        assert "«sig009: text»" in output_content

        # Empty lines created by removal should be cleaned up (e.g., Line 4 should not leave a blank line)
        assert "Only an icon on this line" in output_content
        # Check that there are no blank lines where an entire icon-only line was removed
        assert "\n\n\n" not in output_content  # Should collapse to at most two newlines

        # Verify Step 5.1.1 result
        step_5_1_1 = next((s for s in result.steps if s.step_id == "5.1.1"), None)
        assert step_5_1_1 is not None
        assert step_5_1_1.status == PhaseStatus.SUCCESS
        # Assert each sig is present, order doesn't matter for sets
        assert "Removed markers for icon signatures:" in step_5_1_1.message
        assert "sig010" in step_5_1_1.message
        assert "sig017" in step_5_1_1.message

    def test_remove_icon_markers_no_icons_detected(self, mock_state, phase5_instance):
        output_dir = Path(mock_state.output_dir)
        pdf_name = Path(mock_state.pdf_path).stem

        # Create empty icon_config.json (no icons detected)
        icon_config = {"icon_signatures": []}
        (output_dir / "icon_config.json").write_text(json.dumps(icon_config))

        # Create mock phase4.md input
        input_content = "Line 1: Some text «sig010:A» that should not be removed.\n"
        (output_dir / f"{pdf_name}-phase4.md").write_text(input_content)

        # Execute Phase5
        result = phase5_instance.execute(mock_state)

        # Assertions
        assert result.status == PhaseStatus.SUCCESS
        output_content = (output_dir / f"{pdf_name}-phase5.md").read_text()

        # Icon markers should NOT be removed
        assert "«sig010:A»" in output_content

        # Verify Step 5.1.1 result
        step_5_1_1 = next((s for s in result.steps if s.step_id == "5.1.1"), None)
        assert step_5_1_1 is not None
        assert step_5_1_1.status == PhaseStatus.SKIPPED
        assert (
            "No icon font signatures identified or icon_config.json not found."
            in step_5_1_1.message
        )

    def test_remove_icon_markers_no_font_mapping_file(self, mock_state, phase5_instance):
        output_dir = Path(mock_state.output_dir)
        pdf_name = Path(mock_state.pdf_path).stem

        # DO NOT create font-family-mapping.json

        # Create mock phase4.md input with icon markers
        input_content = "Line 1: Some text «sig010:» with an icon.\n"
        (output_dir / f"{pdf_name}-phase4.md").write_text(input_content)

        # Execute Phase5
        result = phase5_instance.execute(mock_state)

        # Assertions
        assert result.status == PhaseStatus.SUCCESS
        output_content = (output_dir / f"{pdf_name}-phase5.md").read_text()

        # Icon markers should NOT be removed
        assert "«sig010:»" in output_content

        # Verify Step 5.1.1 result
        step_5_1_1 = next((s for s in result.steps if s.step_id == "5.1.1"), None)
        assert step_5_1_1 is not None
        assert step_5_1_1.status == PhaseStatus.SKIPPED
        assert (
            "No icon font signatures identified or icon_config.json not found."
            in step_5_1_1.message
        )

    def test_remove_icon_markers_empty_icon_config_file(self, mock_state, phase5_instance):
        output_dir = Path(mock_state.output_dir)
        pdf_name = Path(mock_state.pdf_path).stem

        # Create an empty icon_config.json
        (output_dir / "icon_config.json").write_text('{"icon_signatures": []}')

        input_content = "Line 1: Some text «sig010:» with an icon.\n"
        (output_dir / f"{pdf_name}-phase4.md").write_text(input_content)

        # Execute Phase5
        result = phase5_instance.execute(mock_state)

        # Assertions
        assert result.status == PhaseStatus.SUCCESS
        output_content = (output_dir / f"{pdf_name}-phase5.md").read_text()
        assert "«sig010:»" in output_content
        step_5_1_1 = next((s for s in result.steps if s.step_id == "5.1.1"), None)
        assert step_5_1_1 is not None
        assert step_5_1_1.status == PhaseStatus.SKIPPED
        assert (
            "No icon font signatures identified or icon_config.json not found."
            in step_5_1_1.message
        )

    def test_remove_icon_markers_invalid_icon_config_json(self, mock_state, phase5_instance):
        output_dir = Path(mock_state.output_dir)
        pdf_name = Path(mock_state.pdf_path).stem

        # Create an invalid icon_config.json (should fall back gracefully)
        (output_dir / "icon_config.json").write_text("invalid json")

        input_content = "Line 1: Some text «sig010:» with an icon.\n"
        (output_dir / f"{pdf_name}-phase4.md").write_text(input_content)

        # Execute Phase5
        result = phase5_instance.execute(mock_state)

        # Assertions
        assert result.status == PhaseStatus.SUCCESS
        output_content = (output_dir / f"{pdf_name}-phase5.md").read_text()
        assert "«sig010:»" in output_content
        step_5_1_1 = next((s for s in result.steps if s.step_id == "5.1.1"), None)
        assert step_5_1_1 is not None
        assert step_5_1_1.status == PhaseStatus.SKIPPED
        assert (
            "No icon font signatures identified or icon_config.json not found."
            in step_5_1_1.message
        )

    def test_remove_whitespace_only_markers(self, mock_state, phase5_instance):
        output_dir = Path(mock_state.output_dir)
        pdf_name = Path(mock_state.pdf_path).stem

        # We need a font mapping, even if it's just to define sig009 as non-icon
        font_mapping_data = {
            "signatures": [
                {
                    "id": "sig009",
                    "family": "Unnamed-T3",
                    "size": 9.6,
                    "weight": "normal",
                    "style": "normal",
                },
                {
                    "id": "sig010",
                    "family": "Unnamed-T3",
                    "size": 10.0,
                    "weight": "normal",
                    "style": "normal",
                    "samples": ["Some Text"],
                },
            ]
        }
        (output_dir / "font-family-mapping.json").write_text(json.dumps(font_mapping_data))

        # Create mock phase4.md input with whitespace-only markers
        input_content = """\
Line with content 1.
«sig009: »
Line with content 2.
«sig009:  »
Another line.
«sig009: \t »
«sig010:   »
«sig010:Some Text» This should remain.
Final line.
"""
        (output_dir / f"{pdf_name}-phase4.md").write_text(input_content)

        # Execute Phase5
        result = phase5_instance.execute(mock_state)

        # Assertions
        assert result.status == PhaseStatus.SUCCESS
        assert (output_dir / f"{pdf_name}-phase5.md").exists()

        output_content = (output_dir / f"{pdf_name}-phase5.md").read_text()

        # Whitespace-only marker lines should be removed
        assert "«sig009: »" not in output_content
        assert "«sig009:  »" not in output_content
        assert "«sig009: \t »" not in output_content
        assert (
            "«sig010:   »" not in output_content
        )  # Ensure it removes any sig with only whitespace content

        # Lines that should remain
        assert "Line with content 1." in output_content
        assert "Line with content 2." in output_content
        assert "Another line." in output_content
        assert "«sig010:Some Text» This should remain." in output_content
        assert "Final line." in output_content

        # Check for collapsed newlines
        assert "\n\n\n" not in output_content  # should be collapsed to at most two newlines

        # Verify Step 5.1.2 result
        step_5_1_2 = next((s for s in result.steps if s.step_id == "5.1.2"), None)
        assert step_5_1_2 is not None
        assert step_5_1_2.status == PhaseStatus.SUCCESS
        assert (
            "Removed lines consisting solely of markers containing only whitespace."
            in step_5_1_2.message
        )

    def test_remove_page_number_markers(self, mock_state, phase5_instance):
        output_dir = Path(mock_state.output_dir)
        pdf_name = Path(mock_state.pdf_path).stem

        # Create mock font-family-mapping.json with a page number signature (sig019)
        # and another digit-only signature that should NOT be removed (low frequency, but now has a label)
        font_mapping_data = {
            "signatures": [
                {
                    "id": "sig019",
                    "family": "Unnamed-T3",
                    "size": 8.7,
                    "weight": "normal",
                    "style": "normal",
                    "samples": ["1"],
                    "candidate_heading": False,
                    "label": None,
                    "frequency": 10,
                },  # Page number
                {
                    "id": "sig020",
                    "family": "Unnamed-T3",
                    "size": 8.7,
                    "weight": "normal",
                    "style": "normal",
                    "samples": ["5"],
                    "candidate_heading": False,
                    "label": "SomeLabel",
                    "frequency": 1,
                },  # NOT a page number (has label)
                {
                    "id": "sig021",
                    "family": "Unnamed-T3",
                    "size": 8.7,
                    "weight": "normal",
                    "style": "normal",
                    "samples": ["A"],
                    "candidate_heading": False,
                    "label": None,
                    "frequency": 10,
                },  # Not digit-only
            ]
        }
        (output_dir / "font-family-mapping.json").write_text(json.dumps(font_mapping_data))

        # Create mock phase4.md input with page number markers
        input_content = """\
Text before page 1.
«sig019:1»
Content on page 1.
«sig020:5» This should remain (low frequency).
More content.
«sig019:2»
End of content.
«sig021:A» This should remain (not digit).
"""
        (output_dir / f"{pdf_name}-phase4.md").write_text(input_content)

        # Execute Phase5
        result = phase5_instance.execute(mock_state)

        # Assertions
        assert result.status == PhaseStatus.SUCCESS
        assert (output_dir / f"{pdf_name}-phase5.md").exists()

        output_content = (output_dir / f"{pdf_name}-phase5.md").read_text()

        # Page number markers should be removed
        assert "«sig019:1»" not in output_content
        assert "«sig019:2»" not in output_content

        # Other content should remain and be checked for existence
        assert "Text before page 1." in output_content
        assert "Content on page 1." in output_content  # Now asserting individual lines
        assert (
            "«sig020:5» This should remain (low frequency)." in output_content
        )  # Now asserting individual lines
        assert "More content." in output_content  # Now asserting individual lines
        assert "End of content." in output_content
        assert "«sig021:A» This should remain (not digit)." in output_content

        # Check for collapsed newlines (should still be true, even with non-merged lines)
        assert "\n\n\n" not in output_content

        # Verify Step 5.1.3 result
        step_5_1_3 = next((s for s in result.steps if s.step_id == "5.1.3"), None)
        assert step_5_1_3 is not None
        assert step_5_1_3.status == PhaseStatus.SUCCESS
        assert "Removed page number markers for signatures: sig019" in step_5_1_3.message

    def test_remove_page_number_markers_skipped(self, mock_state, phase5_instance):
        output_dir = Path(mock_state.output_dir)
        pdf_name = Path(mock_state.pdf_path).stem

        # Create mock font-family-mapping.json WITHOUT page number signatures
        font_mapping_data = {
            "signatures": [
                {
                    "id": "sig009",
                    "family": "Unnamed-T3",
                    "size": 9.6,
                    "weight": "normal",
                    "style": "normal",
                },
            ]
        }
        (output_dir / "font-family-mapping.json").write_text(json.dumps(font_mapping_data))

        # Create mock phase4.md input with a marker that looks like a page number but isn't identified by mapping
        input_content = "Content before. «sig019:1» Content after.\n"
        (output_dir / f"{pdf_name}-phase4.md").write_text(input_content)

        # Execute Phase5
        result = phase5_instance.execute(mock_state)

        # Assertions
        assert result.status == PhaseStatus.SUCCESS
        output_content = (output_dir / f"{pdf_name}-phase5.md").read_text()

        # Page number marker should NOT be removed
        assert "«sig019:1»" in output_content

        # Verify Step 5.1.3 result
        step_5_1_3 = next((s for s in result.steps if s.step_id == "5.1.3"), None)
        assert step_5_1_3 is not None
        assert step_5_1_3.status == PhaseStatus.SKIPPED
        assert (
            "No page number signatures identified or font-family-mapping.json not loaded/valid."
            in step_5_1_3.message
        )
