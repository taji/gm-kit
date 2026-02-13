"""Unit tests for Phase 1 (Image Extraction).

Tests for image extraction, manifest generation, and position tracking.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase1 import Phase1
from gm_kit.pdf_convert.state import ConversionState


class TestPhase1Execute:
    """Test Phase 1 execute method with mocked PyMuPDF."""

    @pytest.fixture
    def mock_state(self, tmp_path):
        """Create a mock ConversionState."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        return ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

    def test__should_create_images_directory__when_executed(self, mock_state, tmp_path):
        """Test that images directory is created during execution."""
        phase = Phase1()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=0)
            mock_open.return_value = mock_doc

            result = phase.execute(mock_state)

        images_dir = Path(mock_state.output_dir) / "images"
        assert images_dir.exists()
        assert result.status == PhaseStatus.SUCCESS

    def test__should_extract_images_and_create_manifest__when_pdf_has_images(
        self, mock_state, tmp_path
    ):
        """Test that images are extracted and manifest is created."""
        phase = Phase1()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            # Mock page with one image
            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.get_image_rects.return_value = [MagicMock(x0=10, y0=20, width=100, height=50)]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)

            # Mock image extraction
            mock_doc.extract_image.return_value = {"image": b"fake_image_data", "ext": "png"}

            mock_open.return_value = mock_doc

            result = phase.execute(mock_state)
            assert result.status == PhaseStatus.SUCCESS

        # Check image file was created
        img_path = Path(mock_state.output_dir) / "images" / "page001_img01.png"
        assert img_path.exists()

        # Check manifest was created
        manifest_path = Path(mock_state.output_dir) / "images" / "image-manifest.json"
        assert manifest_path.exists()

        # Check manifest content
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["total_count"] == 1
        assert len(manifest["images"]) == 1
        assert manifest["images"][0]["page"] == 1
        assert manifest["images"][0]["filename"] == "page001_img01.png"
        assert manifest["images"][0]["position"]["x"] == 10
        assert manifest["images"][0]["position"]["y"] == 20

    def test__should_handle_multiple_pages_with_multiple_images(self, mock_state, tmp_path):
        """Test extraction of multiple images across multiple pages."""
        phase = Phase1()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=2)

            # Page 1 with 2 images
            mock_page1 = MagicMock()
            mock_page1.get_images.return_value = [(1,), (2,)]
            mock_page1.get_image_rects.side_effect = [
                [MagicMock(x0=10, y0=20, width=100, height=50)],
                [MagicMock(x0=30, y0=40, width=80, height=60)],
            ]

            # Page 2 with 1 image
            mock_page2 = MagicMock()
            mock_page2.get_images.return_value = [(3,)]
            mock_page2.get_image_rects.return_value = [
                MagicMock(x0=50, y0=60, width=120, height=80)
            ]

            def get_page(idx):
                return [mock_page1, mock_page2][idx]

            mock_doc.__getitem__ = MagicMock(side_effect=get_page)
            mock_doc.extract_image.return_value = {"image": b"fake_image_data", "ext": "png"}

            mock_open.return_value = mock_doc

            phase.execute(mock_state)

        # Check all 3 images were extracted
        images_dir = Path(mock_state.output_dir) / "images"
        assert (images_dir / "page001_img01.png").exists()
        assert (images_dir / "page001_img02.png").exists()
        assert (images_dir / "page002_img01.png").exists()

        # Check manifest
        with open(images_dir / "image-manifest.json") as f:
            manifest = json.load(f)

        assert manifest["total_count"] == 3
        assert len(manifest["images"]) == 3

    def test__should_handle_pdf_with_no_images(self, mock_state, tmp_path):
        """Test handling of PDF without any images."""
        phase = Phase1()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=2)

            mock_page = MagicMock()
            mock_page.get_images.return_value = []
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)

            mock_open.return_value = mock_doc

            phase.execute(mock_state)

        # Check manifest was created with empty images array
        manifest_path = Path(mock_state.output_dir) / "images" / "image-manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["total_count"] == 0
        assert manifest["images"] == []

    def test__should_return_error__when_pdf_open_fails(self, mock_state):
        """Test error handling when PDF cannot be opened."""
        phase = Phase1()

        with patch("fitz.open", side_effect=Exception("PDF corrupted")):
            result = phase.execute(mock_state)

        assert result.status == PhaseStatus.ERROR
        assert "PDF corrupted" in result.errors[0]

    def test__should_return_error__when_image_extraction_fails(self, mock_state):
        """Test error handling when image extraction fails mid-process."""
        phase = Phase1()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.get_image_rects.return_value = [MagicMock(x0=0, y0=0, width=10, height=10)]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)
            mock_doc.extract_image.side_effect = Exception("Cannot extract image")

            mock_open.return_value = mock_doc

            result = phase.execute(mock_state)

        assert result.status == PhaseStatus.ERROR


class TestPhase1ManifestFormat:
    """Test image manifest format and content."""

    def test__manifest_should_have_required_fields(self, tmp_path):
        """Test that manifest entries contain all required fields."""
        phase = Phase1()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path))

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.get_image_rects.return_value = [
                MagicMock(x0=10.5, y0=20.25, width=100, height=50.75)
            ]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)
            mock_doc.extract_image.return_value = {"image": b"fake_image_data", "ext": "png"}

            mock_open.return_value = mock_doc

            phase.execute(state)

        manifest_path = tmp_path / "images" / "image-manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Check manifest structure
        assert "images" in manifest
        assert "total_count" in manifest

        entry = manifest["images"][0]
        required_fields = {"page", "filename", "position", "alt_text"}
        assert required_fields.issubset(set(entry.keys()))

        # Check position has required fields
        position_fields = {"x", "y", "width", "height"}
        assert position_fields.issubset(set(entry["position"].keys()))

    def test__manifest_positions_should_be_floats(self, tmp_path):
        """Test that position values are stored as floats."""
        phase = Phase1()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path))

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            rect_mock = MagicMock()
            rect_mock.x0 = 10.0
            rect_mock.y0 = 20.0
            rect_mock.width = 100.0
            rect_mock.height = 50.0

            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.get_image_rects.return_value = [rect_mock]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)
            mock_doc.extract_image.return_value = {"image": b"fake_image_data", "ext": "png"}

            mock_open.return_value = mock_doc

            phase.execute(state)

        manifest_path = tmp_path / "images" / "image-manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        pos = manifest["images"][0]["position"]
        assert isinstance(pos["x"], float)
        assert isinstance(pos["y"], float)
        assert isinstance(pos["width"], float)
        assert isinstance(pos["height"], float)


class TestPhase1StepResults:
    """Test step-by-step results from Phase 1."""

    def test__should_report_step_1_1_success__when_images_found(self, tmp_path):
        """Test that step 1.1 reports success when images are found."""
        phase = Phase1()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path))

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.get_image_rects.return_value = [MagicMock(x0=0, y0=0, width=10, height=10)]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)
            mock_doc.extract_image.return_value = {"image": b"data", "ext": "png"}

            mock_open.return_value = mock_doc

            result = phase.execute(state)

        step_1_1 = [s for s in result.steps if s.step_id == "1.1"]
        assert len(step_1_1) == 1
        assert step_1_1[0].status == PhaseStatus.SUCCESS
        assert step_1_1[0].message and "1" in step_1_1[0].message  # Should mention 1 image

    def test__should_report_step_1_2_success__when_images_extracted(self, tmp_path):
        """Test that step 1.2 reports success when images are extracted."""
        phase = Phase1()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path))

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.get_image_rects.return_value = [MagicMock(x0=0, y0=0, width=10, height=10)]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)
            mock_doc.extract_image.return_value = {"image": b"data", "ext": "png"}

            mock_open.return_value = mock_doc

            result = phase.execute(state)

        step_1_2 = [s for s in result.steps if s.step_id == "1.2"]
        assert len(step_1_2) == 1
        assert step_1_2[0].status == PhaseStatus.SUCCESS
        assert (
            step_1_2[0].message and "1" in step_1_2[0].message
        )  # Should mention 1 image extracted

    def test__should_report_step_1_4_success__when_manifest_created(self, tmp_path):
        """Test that step 1.4 reports success when manifest is created."""
        phase = Phase1()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path))

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            mock_page = MagicMock()
            mock_page.get_images.return_value = []
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)
            mock_open.return_value = mock_doc

            result = phase.execute(state)

        step_1_4 = [s for s in result.steps if s.step_id == "1.4"]
        assert len(step_1_4) == 1
        assert step_1_4[0].status == PhaseStatus.SUCCESS
        assert step_1_4[0].message and "image-manifest.json" in step_1_4[0].message
