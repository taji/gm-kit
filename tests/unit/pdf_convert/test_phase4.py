"""Unit tests for Phase 4 text extraction and spacing (T025)."""

import json

import pytest

from gm_kit.pdf_convert.phases.phase4 import _build_font_to_id_mapping, _escape_marker_chars


class TestEscapeMarkerChars:
    """Test marker character escaping."""

    def test_should_escape_left_angle_bracket(self):
        """Left angle bracket « should be escaped."""
        result = _escape_marker_chars("Hello «world»")
        assert result == "Hello \\«world\\»"

    def test_should_escape_right_angle_bracket(self):
        """Right angle bracket » should be escaped."""
        result = _escape_marker_chars("Test»value")
        assert result == "Test\\»value"

    def test_should_not_modify_regular_text(self):
        """Regular text without markers should be unchanged."""
        text = "Hello world! This is normal text."
        result = _escape_marker_chars(text)
        assert result == text


class TestBuildFontToIdMapping:
    """Test font signature mapping construction."""

    def test_should_build_mapping_from_valid_json(self, tmp_path):
        """Should create mapping from family|size|weight|style to sig ID."""
        mapping_data = {
            "signatures": [
                {
                    "id": "sig001",
                    "family": "Arial",
                    "size": 12.0,
                    "weight": "normal",
                    "style": "normal",
                },
                {
                    "id": "sig002",
                    "family": "Arial",
                    "size": 14.0,
                    "weight": "bold",
                    "style": "normal",
                },
            ]
        }
        mapping_path = tmp_path / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping_data))

        result = _build_font_to_id_mapping(mapping_path)

        assert result == {
            "Arial|12.0|normal|normal": "sig001",
            "Arial|14.0|bold|normal": "sig002",
        }

    def test_should_return_empty_dict_for_missing_file(self, tmp_path):
        """Should return empty dict if mapping file doesn't exist."""
        mapping_path = tmp_path / "nonexistent.json"
        result = _build_font_to_id_mapping(mapping_path)
        assert result == {}

    def test_should_return_empty_dict_for_invalid_json(self, tmp_path):
        """Should return empty dict if JSON is malformed."""
        mapping_path = tmp_path / "invalid.json"
        mapping_path.write_text("not valid json")
        result = _build_font_to_id_mapping(mapping_path)
        assert result == {}


class TestPhase4Execute:
    """Test Phase 4 execution with various PDF structures."""

    @pytest.fixture
    def setup_conversion_state(self, tmp_path):
        """Create a ConversionState with necessary files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        preprocessed_dir = output_dir / "preprocessed"
        preprocessed_dir.mkdir()

        # Create minimal mapping file
        mapping_data = {
            "signatures": [
                {
                    "id": "sig001",
                    "family": "Arial",
                    "size": 12.0,
                    "weight": "normal",
                    "style": "normal",
                },
                {
                    "id": "sig002",
                    "family": "Arial",
                    "size": 14.0,
                    "weight": "bold",
                    "style": "normal",
                },
            ]
        }
        (output_dir / "font-family-mapping.json").write_text(json.dumps(mapping_data))

        pdf_path = preprocessed_dir / "test-no-images.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")

        return str(pdf_path), str(output_dir)


class TestSpanProcessingLogic:
    """Test the span grouping and spacing logic (extracted for unit testing)."""

    def _simulate_span_processing(self, spans, font_to_id):  # noqa: PLR0912
        """Simulate Phase 4 span processing logic.

        Args:
            spans: List of dicts with 'text', 'font', 'size', 'flags'
            font_to_id: Mapping from font_key to sig_id

        Returns:
            List of marker strings
        """
        line_groups = []
        current_sig_id = None
        current_text_parts = []

        for span in spans:
            span_text = span.get("text", "")
            if not span_text:
                continue

            font = span.get("font", "Unknown")
            size = round(span.get("size", 0), 1)
            flags = span.get("flags", 0)
            weight = "bold" if flags & 1 else "normal"
            style = "italic" if flags & 2 else "normal"

            font_key = f"{font}|{size}|{weight}|{style}"
            sig_id = font_to_id.get(font_key)
            escaped_text = span_text.replace("«", "\\«").replace("»", "\\»")
            is_whitespace = not span_text.strip()

            if sig_id:
                if is_whitespace:
                    if current_sig_id and current_sig_id != sig_id and current_text_parts:
                        group_text = "".join(current_text_parts)
                        line_groups.append(f"«{current_sig_id}:{group_text}»")
                        current_sig_id = None
                        current_text_parts = []

                    if sig_id == current_sig_id:
                        current_text_parts.append(escaped_text)
                    else:
                        if current_text_parts:
                            group_text = "".join(current_text_parts)
                            line_groups.append(f"«{current_sig_id}:{group_text}»")
                        current_sig_id = sig_id
                        current_text_parts = [escaped_text]

                elif sig_id == current_sig_id:
                    if (
                        current_text_parts
                        and not current_text_parts[-1].endswith(" ")
                        and not escaped_text.startswith(" ")
                    ):
                        current_text_parts.append(" ")
                    current_text_parts.append(escaped_text)
                else:
                    if current_sig_id and current_text_parts:
                        group_text = "".join(current_text_parts)
                        line_groups.append(f"«{current_sig_id}:{group_text}»")
                    elif current_text_parts:
                        line_groups.append("".join(current_text_parts))
                    current_sig_id = sig_id
                    current_text_parts = [escaped_text]
            else:
                if current_sig_id and current_text_parts:
                    group_text = "".join(current_text_parts)
                    line_groups.append(f"«{current_sig_id}:{group_text}»")
                    current_sig_id = None
                    current_text_parts = []

                if (
                    line_groups
                    and not line_groups[-1].endswith(" ")
                    and not escaped_text.startswith(" ")
                ):
                    line_groups.append(" ")
                line_groups.append(escaped_text)

        if current_sig_id and current_text_parts:
            group_text = "".join(current_text_parts)
            line_groups.append(f"«{current_sig_id}:{group_text}»")
        elif current_text_parts:
            line_groups.append("".join(current_text_parts))

        return line_groups

    def test_should_add_space_between_consecutive_words_same_signature(self):
        """Words with same signature should be separated by space."""
        font_to_id = {"Arial|12.0|normal|normal": "sig001"}
        spans = [
            {"text": "Hello", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": "world", "font": "Arial", "size": 12.0, "flags": 0},
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        assert result == ["«sig001:Hello world»"]

    def test_should_preserve_trailing_space_in_span(self):
        """If span already has trailing space, don't add another."""
        font_to_id = {"Arial|12.0|normal|normal": "sig001"}
        spans = [
            {"text": "Hello ", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": "world", "font": "Arial", "size": 12.0, "flags": 0},
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        assert result == ["«sig001:Hello world»"]

    def test_should_handle_whitespace_spans_separately(self):
        """Whitespace-only spans should be preserved in their own groups."""
        font_to_id = {
            "Arial|12.0|normal|normal": "sig001",
            "Arial|14.0|normal|normal": "sig002",  # Different signature for spaces
        }
        spans = [
            {"text": "Hello", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": " ", "font": "Arial", "size": 14.0, "flags": 0},
            {"text": "world", "font": "Arial", "size": 12.0, "flags": 0},
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        # Whitespace with different signature gets its own marker
        assert result == ["«sig001:Hello»", "«sig002: »", "«sig001:world»"]

    def test_should_preserve_multiple_consecutive_spaces(self):
        """Multiple consecutive spaces should be preserved."""
        font_to_id = {"Arial|12.0|normal|normal": "sig001"}
        spans = [
            {"text": "Hello", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": " ", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": " ", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": "world", "font": "Arial", "size": 12.0, "flags": 0},
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        # Both space spans are preserved (2 spaces total)
        assert result == ["«sig001:Hello  world»"]

    def test_should_handle_different_signatures_correctly(self):
        """Words with different signatures should be in separate groups."""
        font_to_id = {
            "Arial|12.0|normal|normal": "sig001",
            "Arial|14.0|bold|normal": "sig002",
        }
        spans = [
            {"text": "Normal", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": "Bold", "font": "Arial", "size": 14.0, "flags": 1},  # Bold flag
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        assert result == ["«sig001:Normal»", "«sig002:Bold»"]

    def test_should_handle_unmarked_text(self):
        """Text without signature mapping should be unmarked."""
        font_to_id = {"Arial|12.0|normal|normal": "sig001"}
        spans = [
            {"text": "Hello", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": "unknown", "font": "Times", "size": 10.0, "flags": 0},  # Not in mapping
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        assert result == ["«sig001:Hello»", " ", "unknown"]

    def test_should_escape_marker_characters(self):
        """Angle brackets in text should be escaped."""
        font_to_id = {"Arial|12.0|normal|normal": "sig001"}
        spans = [
            {"text": "«Hello»", "font": "Arial", "size": 12.0, "flags": 0},
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        assert result == ["«sig001:\\«Hello\\»»"]

    def test_should_handle_empty_spans(self):
        """Empty spans should be skipped."""
        font_to_id = {"Arial|12.0|normal|normal": "sig001"}
        spans = [
            {"text": "Hello", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": "", "font": "Arial", "size": 12.0, "flags": 0},
            {"text": "world", "font": "Arial", "size": 12.0, "flags": 0},
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        assert result == ["«sig001:Hello world»"]

    def test_should_handle_complex_pdf_structure(self):
        """Simulate the actual Homebrewery PDF structure with mixed signatures."""
        font_to_id = {
            "SolberaImitation|99.2|normal|normal": "sig001",  # Decorative W
            "Unnamed-T3|6.8|normal|normal": "sig022",  # Body text
            "Unnamed-T3|9.6|normal|normal": "sig009",  # Spaces
        }
        spans = [
            {"text": "W", "font": "SolberaImitation", "size": 99.2, "flags": 0},
            {"text": "elcome", "font": "Unnamed-T3", "size": 6.8, "flags": 0},
            {"text": " ", "font": "Unnamed-T3", "size": 9.6, "flags": 0},
            {"text": "traveler", "font": "Unnamed-T3", "size": 6.8, "flags": 0},
        ]
        result = self._simulate_span_processing(spans, font_to_id)
        assert result == [
            "«sig001:W»",
            "«sig022:elcome»",
            "«sig009: »",
            "«sig022:traveler»",
        ]
