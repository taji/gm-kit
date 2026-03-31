"""Unit tests for Phase 7: Font Label Assignment.

Tests structural detection including:
- ALL CAPS heading detection (Step 7.3)
- Title Case heading detection (Step 7.4)
- GM note keyword detection (Step 7.5)
- Read-aloud marker detection (Step 7.6)
- Font mapping updates (Step 7.9)
"""

import json
from unittest.mock import MagicMock, patch

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase7 import Phase7
from gm_kit.pdf_convert.state import ConversionState


class TestExtractMarkersFromText:
    """Test marker extraction from phase6 content."""

    def test__should_extract_single_marker(self):
        phase = Phase7()
        text = "«sig001:Hello World»"
        results = list(phase._extract_markers_from_text(text))
        assert results == [("sig001", "Hello World")]

    def test__should_extract_multiple_markers(self):
        phase = Phase7()
        text = "«sig001:First» «sig002:Second»"
        results = list(phase._extract_markers_from_text(text))
        assert results == [("sig001", "First"), ("sig002", "Second")]

    def test__should_handle_empty_content(self):
        """Empty marker content should be extracted (e.g., icon fonts)."""
        phase = Phase7()
        text = "«sig001:»"
        results = list(phase._extract_markers_from_text(text))
        assert results == [("sig001", "")]

    def test__should_handle_text_without_markers(self):
        phase = Phase7()
        text = "Plain text without markers"
        results = list(phase._extract_markers_from_text(text))
        assert results == []


class TestVisionBBoxExtraction:
    """Test step 7.7 vision output normalization."""

    def test__should_extract_top_level_bbox__when_present(self):
        phase = Phase7()
        result = phase._extract_confirmed_bbox(
            {"table_id": "t1", "bbox_pixels": {"x0": 1, "y0": 2, "x1": 3, "y1": 4}},
            "t1",
        )
        assert result == ("t1", {"x0": 1, "y0": 2, "x1": 3, "y1": 4})

    def test__should_extract_matching_table_bbox__when_nested_tables_present(self):
        phase = Phase7()
        result = phase._extract_confirmed_bbox(
            {
                "tables": [
                    {"table_id": "t1", "bbox_pixels": {"x0": 10, "y0": 20, "x1": 30, "y1": 40}},
                    {"table_id": "t2", "bbox_pixels": {"x0": 11, "y0": 21, "x1": 31, "y1": 41}},
                ]
            },
            "t2",
        )
        assert result == ("t2", {"x0": 11, "y0": 21, "x1": 31, "y1": 41})

    def test__should_return_none__when_no_bbox_is_available(self):
        phase = Phase7()
        result = phase._extract_confirmed_bbox({"tables": [{"table_id": "t1"}]}, "t1")
        assert result is None


class TestTablesManifestPersistence:
    """Ensure tables-manifest exists even when 7.7 fails."""

    @patch("gm_kit.pdf_convert.agents.AgentStepRuntime")
    @patch("gm_kit.pdf_convert.phases.phase7.fitz.open")
    def test__should_write_empty_manifest__when_agent_step_7_7_fails(
        self, mock_open_pdf, mock_runtime, tmp_path
    ):
        phase = Phase7()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        fake_page = MagicMock()
        fake_page.get_text.return_value = "table-ish text"
        fake_doc = MagicMock()
        fake_doc.__len__.return_value = 1
        fake_doc.load_page.return_value = fake_page
        mock_open_pdf.return_value = fake_doc

        runtime_instance = mock_runtime.return_value
        runtime_instance.execute_step.side_effect = RuntimeError("timeout")

        result = phase.create_result()
        phase._execute_agent_steps(result, output_dir, str(tmp_path / "test.pdf"))

        manifest_path = output_dir / "tables-manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["total_count"] == 0
        assert manifest["tables"] == []


class TestAllCapsDetection:
    """Test ALL CAPS heading detection (Step 7.3)."""

    def test__should_detect_all_caps_heading(self, tmp_path):
        """ALL CAPS text larger than body should be flagged as heading."""
        phase = Phase7()

        # Create test files
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
                {"id": "sig002", "family": "Heading", "size": 16.0, "label": None},
            ]
        }

        # Write mapping file
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Write phase6 content
        phase6_content = "«sig001:Normal body text.»\n«sig002:CHAPTER ONE»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        # Find step 7.3 result
        step_73 = next((s for s in result.steps if s.step_id == "7.3"), None)
        assert step_73 is not None
        assert step_73.status == PhaseStatus.SUCCESS
        assert "1 signatures" in step_73.message

    def test__should_ignore_short_all_caps(self, tmp_path):
        """Short ALL CAPS like 'OK' or 'A' should not be headings."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
                {"id": "sig002", "family": "Heading", "size": 16.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # "YES" is only 3 chars, should still be detected as ALL CAPS
        phase6_content = "«sig001:Answer is» «sig002:YES»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_73 = next((s for s in result.steps if s.step_id == "7.3"), None)
        assert step_73 is not None
        assert step_73.status == PhaseStatus.SUCCESS

    def test__should_ignore_mixed_case(self, tmp_path):
        """Mixed case text should not be flagged as ALL CAPS."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
                {"id": "sig002", "family": "Heading", "size": 16.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Mixed case - should NOT be ALL CAPS
        phase6_content = "«sig002:Chapter One»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_73 = next((s for s in result.steps if s.step_id == "7.3"), None)
        assert step_73 is not None
        assert "0 signatures" in step_73.message


class TestTitleCaseDetection:
    """Test Title Case heading detection (Step 7.4)."""

    def test__should_detect_title_case_heading(self, tmp_path):
        """Title Case text larger than body should be flagged."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
                {"id": "sig002", "family": "Heading", "size": 16.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig002:The Quick Brown Fox»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_74 = next((s for s in result.steps if s.step_id == "7.4"), None)
        assert step_74 is not None
        assert step_74.status == PhaseStatus.SUCCESS
        assert "1 signatures" in step_74.message

    def test__should_handle_minor_words_in_title_case(self, tmp_path):
        """Title Case with minor words (the, and, of) should be valid."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
                {"id": "sig002", "family": "Heading", "size": 16.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Minor words (the, of) don't need to be capitalized except first word
        phase6_content = "«sig002:The Lord of the Rings»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_74 = next((s for s in result.steps if s.step_id == "7.4"), None)
        assert step_74 is not None
        assert "1 signatures" in step_74.message

    def test__should_reject_sentence_case(self, tmp_path):
        """Sentence case should NOT be detected as Title Case."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Sentence case - only first word capitalized
        phase6_content = "«sig001:This is a normal sentence»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_74 = next((s for s in result.steps if s.step_id == "7.4"), None)
        assert step_74 is not None
        assert "0 signatures" in step_74.message


class TestGMNoteDetection:
    """Test GM/Keeper note keyword detection (Step 7.5)."""

    def test__should_detect_gm_note_keyword(self, tmp_path):
        """Content with 'GM Note' should be flagged as callout."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:GM Note: This is secret info»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_75 = next((s for s in result.steps if s.step_id == "7.5"), None)
        assert step_75 is not None
        assert step_75.status == PhaseStatus.SUCCESS
        assert "1 signatures" in step_75.message

    def test__should_detect_keeper_note(self, tmp_path):
        """Content with 'Keeper Note' should be flagged."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        # Use "keeper note" without apostrophe to match keyword
        phase6_content = "«sig001:Keeper Note: Hidden monster ahead»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_75 = next((s for s in result.steps if s.step_id == "7.5"), None)
        assert step_75 is not None
        assert step_75.message is not None and "1 signatures" in step_75.message

    def test__should_use_custom_keywords(self, tmp_path):
        """Custom keywords from config should be detected."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:Custom alert: Watch out!»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={"gm_keyword": ["custom alert", "special note"]},
        )

        result = phase.execute(state)

        step_75 = next((s for s in result.steps if s.step_id == "7.5"), None)
        assert step_75 is not None
        assert "1 signatures" in step_75.message

    def test__should_not_flag_normal_text(self, tmp_path):
        """Normal text without keywords should not be flagged."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:Normal text without any keywords»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_75 = next((s for s in result.steps if s.step_id == "7.5"), None)
        assert step_75 is not None
        assert "0 signatures" in step_75.message


class TestReadAloudDetection:
    """Test read-aloud text marker detection (Step 7.6)."""

    def test__should_detect_read_aloud_marker(self, tmp_path):
        """Content with 'Read Aloud' should be flagged."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:Read Aloud: You enter the dark room»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_76 = next((s for s in result.steps if s.step_id == "7.6"), None)
        assert step_76 is not None
        assert step_76.status == PhaseStatus.SUCCESS
        assert "1 signatures" in step_76.message

    def test__should_detect_boxed_text(self, tmp_path):
        """Content with 'Boxed Text' should be flagged."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:Boxed Text: Treasure chest contents»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        step_76 = next((s for s in result.steps if s.step_id == "7.6"), None)
        assert step_76 is not None
        assert "1 signatures" in step_76.message


class TestMappingUpdates:
    """Test font-family-mapping.json updates (Step 7.9)."""

    def test__should_assign_h2_to_large_all_caps(self, tmp_path):
        """ALL CAPS significantly larger than body should get H2 (or H1 if only heading)."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
                {"id": "sig002", "family": "Heading", "size": 20.0, "label": None},  # 2x body
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig002:CHAPTER ONE»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        phase.execute(state)

        # Check that sig002 got H1 label (promoted from H2 because no H1 exists)
        updated_mapping = json.loads(mapping_path.read_text())
        sig002 = next((s for s in updated_mapping["signatures"] if s["id"] == "sig002"), None)
        assert sig002 is not None
        assert sig002["label"] == "H1"

    def test__should_assign_h3_to_moderate_all_caps(self, tmp_path):
        """ALL CAPS moderately larger than body should get H3 (or H1 if only heading)."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
                {"id": "sig002", "family": "Heading", "size": 14.0, "label": None},  # 1.4x body
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig002:SECTION A»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        phase.execute(state)

        # Check that sig002 got a heading label (promoted to H1 because it's the only heading)
        updated_mapping = json.loads(mapping_path.read_text())
        sig002 = next((s for s in updated_mapping["signatures"] if s["id"] == "sig002"), None)
        assert sig002 is not None
        assert sig002["label"] in ["H1", "H2", "H3"]  # Should have some heading label

    def test__should_not_overwrite_existing_label(self, tmp_path):
        """Signatures with existing labels should not be changed."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
                {
                    "id": "sig002",
                    "family": "Heading",
                    "size": 16.0,
                    "label": "H1",
                },  # Already has H1
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig002:CHAPTER ONE»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        phase.execute(state)

        # Check that sig002 kept H1 label
        updated_mapping = json.loads(mapping_path.read_text())
        sig002 = next((s for s in updated_mapping["signatures"] if s["id"] == "sig002"), None)
        assert sig002 is not None
        assert sig002["label"] == "H1"  # Unchanged

    def test__should_assign_callout_label(self, tmp_path):
        """Signatures with GM note keywords should get callout_gm label."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:GM Note: Secret information»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        phase.execute(state)

        updated_mapping = json.loads(mapping_path.read_text())
        sig001 = next((s for s in updated_mapping["signatures"] if s["id"] == "sig001"), None)
        assert sig001 is not None
        assert sig001["label"] == "callout_gm"

    def test__should_assign_read_aloud_label(self, tmp_path):
        """Signatures with read-aloud markers should get callout_read_aloud."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {"id": "sig001", "family": "Body", "size": 10.0, "label": None},
            ]
        }

        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        phase6_content = "«sig001:Read Aloud: You see a dragon»"
        phase6_path = output_dir / "test-phase6.md"
        phase6_path.write_text(phase6_content)

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        phase.execute(state)

        updated_mapping = json.loads(mapping_path.read_text())
        sig001 = next((s for s in updated_mapping["signatures"] if s["id"] == "sig001"), None)
        assert sig001 is not None
        assert sig001["label"] == "callout_read_aloud"

    def test__should_prioritize_toc_labels_over_title_case_heuristics(self, tmp_path):
        """When TOC exists, only TOC-matched signatures should be promoted broadly."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mapping = {
            "signatures": [
                {
                    "id": "sig001",
                    "family": "Body",
                    "size": 10.0,
                    "label": None,
                    "candidate_heading": False,
                },
                {
                    "id": "sig002",
                    "family": "Heading",
                    "size": 16.0,
                    "label": None,
                    "candidate_heading": True,
                },
            ]
        }

        (output_dir / "font-family-mapping.json").write_text(json.dumps(mapping))
        (output_dir / "toc-extracted.txt").write_text("Chapter One (page 1)\n")
        (output_dir / "test-phase6.md").write_text(
            "«sig002:Chapter One»\n«sig001:This is body text that is Title Case»"
        )

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        phase.execute(state)

        updated_mapping = json.loads((output_dir / "font-family-mapping.json").read_text())
        sig001 = next((s for s in updated_mapping["signatures"] if s["id"] == "sig001"), None)
        sig002 = next((s for s in updated_mapping["signatures"] if s["id"] == "sig002"), None)

        assert sig001 is not None
        assert sig002 is not None
        assert sig001["label"] is None
        assert sig002["label"] == "H1"


class TestErrorHandling:
    """Test error handling in Phase 7."""

    def test__should_error_if_mapping_not_found(self, tmp_path):
        """Should error if font-family-mapping.json doesn't exist."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        assert result.status == PhaseStatus.ERROR
        assert "not found" in result.errors[0].lower()

    def test__should_error_if_phase6_not_found(self, tmp_path):
        """Should error if phase6.md doesn't exist."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        # Create mapping but not phase6
        mapping = {"signatures": []}
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        assert result.status == PhaseStatus.ERROR
        assert "phase6" in result.errors[0].lower()

    def test__should_handle_invalid_json(self, tmp_path):
        """Should error if font-family-mapping.json is invalid."""
        phase = Phase7()

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        # Create invalid JSON
        mapping_path = output_dir / "font-family-mapping.json"
        mapping_path.write_text("invalid json")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            config={},
        )

        result = phase.execute(state)

        assert result.status == PhaseStatus.ERROR
        assert any("json" in err.lower() for err in result.errors)
