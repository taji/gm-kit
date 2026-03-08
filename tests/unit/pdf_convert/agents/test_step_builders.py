"""Tests for step builders."""


from gm_kit.pdf_convert.agents.step_builders import (
    _extract_domain_terms,
    build_ocr_correction_payload,
    build_sentence_boundary_payload,
    build_structural_clarity_payload,
    build_toc_parsing_payload,
    build_toc_validation_payload,
)


class TestContentRepairPayloads:
    """Test content repair step payloads."""

    def test_toc_parsing_payload(self, tmp_path):
        """Should build TOC parsing payload."""
        payload = build_toc_parsing_payload(
            toc_text="Contents\nChapter 1 (page 5)", total_pages=50, workspace=str(tmp_path)
        )

        assert payload["step_id"] == "3.2"
        assert payload["context"]["toc_text"] == "Contents\nChapter 1 (page 5)"
        assert payload["context"]["total_pages"] == 50
        assert payload["context"]["task"] == "parse_visual_toc"

    def test_sentence_boundary_payload(self, tmp_path):
        """Should build sentence boundary payload."""
        boundaries = [{"page": 5, "line": 23}]

        payload = build_sentence_boundary_payload(
            phase4_file="/path/to/phase4.md", chunk_boundaries=boundaries, workspace=str(tmp_path)
        )

        assert payload["step_id"] == "4.5"
        assert payload["input_artifacts"]["phase_file"] == "/path/to/phase4.md"
        assert payload["context"]["chunk_boundaries"] == boundaries

    def test_ocr_correction_payload(self, tmp_path):
        """Should build OCR correction payload."""
        font_sigs = {
            "sig001": {"samples": ["Beholder", "Mind Flayer"]},
        }

        payload = build_ocr_correction_payload(
            phase6_file="/path/to/phase6.md", font_signatures=font_sigs, workspace=str(tmp_path)
        )

        assert payload["step_id"] == "6.4"
        assert "preserve_terms" in payload["context"]
        assert "BEHOLDER" in payload["context"]["preserve_terms"]


class TestQualityAssessmentPayloads:
    """Test quality assessment step payloads."""

    def test_structural_clarity_payload(self, tmp_path):
        """Should build structural clarity payload."""
        payload = build_structural_clarity_payload(
            phase8_file="/path/to/phase8.md", toc_file="/path/to/toc.txt", workspace=str(tmp_path)
        )

        assert payload["step_id"] == "9.2"
        assert payload["input_artifacts"]["phase8_file"] == "/path/to/phase8.md"
        assert "toc_file" in payload["context"]

    def test_toc_validation_with_font_mapping(self, tmp_path):
        """Should include font mapping for TOC validation."""
        mapping_file = tmp_path / "font-mapping.json"
        mapping_file.write_text("{}")

        payload = build_toc_validation_payload(
            phase8_file="/path/to/phase8.md",
            toc_file="/path/to/toc.txt",
            font_family_mapping=str(mapping_file),
            workspace=str(tmp_path),
        )

        assert payload["step_id"] == "9.7"
        assert "font_family_mapping" in payload["optional_artifacts"]


class TestDomainTermExtraction:
    """Test domain term extraction from font signatures."""

    def test_extracts_common_ttrpg_terms(self):
        """Should include common TTRPG abbreviations."""
        terms = _extract_domain_terms({})

        assert "AC" in terms
        assert "HP" in terms
        assert "DC" in terms
        assert "STR" in terms

    def test_extracts_from_samples(self):
        """Should extract terms from font signature samples."""
        font_sigs = {
            "sig001": {"samples": ["Dragon", "Dungeon Master"]},
        }

        terms = _extract_domain_terms(font_sigs)

        assert "DRAGON" in terms
        assert "DUNGEON" in terms
        assert "MASTER" in terms
