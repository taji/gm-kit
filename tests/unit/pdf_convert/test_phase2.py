"""Unit tests for Phase 2 (Image Removal).

Tests for creating text-only PDF by covering images with white rectangles.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase2 import Phase2
from gm_kit.pdf_convert.state import ConversionState


class TestPhase2Execute:
    """Test Phase 2 execute method with mocked PyMuPDF."""

    @pytest.fixture
    def mock_state(self, tmp_path):
        """Create a mock ConversionState."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        return ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

    def test__should_create_preprocessed_directory__when_executed(self, mock_state, tmp_path):
        """Test that preprocessed directory is created during execution."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=0)
            mock_open.return_value = mock_doc

            phase.execute(mock_state)

        preprocessed_dir = Path(mock_state.output_dir) / "preprocessed"
        assert preprocessed_dir.exists()

    def test__should_cover_images_with_white_rectangles__when_pdf_has_images(
        self, mock_state, tmp_path
    ):
        """Test that images are covered with white rectangles."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            # Mock page with one image
            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_rect = MagicMock()
            mock_page.get_image_rects.return_value = [mock_rect]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)

            mock_open.return_value = mock_doc

            phase.execute(mock_state)

        # Verify draw_rect was called to cover the image
        mock_page.draw_rect.assert_called_once_with(mock_rect, color=(1, 1, 1), fill=(1, 1, 1))

    def test__should_save_output_pdf__when_processing_complete(self, mock_state, tmp_path):
        """Test that output PDF is saved after processing."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            mock_page = MagicMock()
            mock_page.get_images.return_value = []
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)

            mock_open.return_value = mock_doc

            phase.execute(mock_state)

        # Verify save was called
        expected_output = tmp_path / "preprocessed" / "test-no-images.pdf"
        mock_doc.save.assert_called_once_with(expected_output)
        mock_doc.close.assert_called_once()

    def test__should_handle_multiple_images_on_same_page(self, mock_state, tmp_path):
        """Test covering multiple images on the same page."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            mock_page = MagicMock()
            # Two different images (different xrefs)
            mock_page.get_images.return_value = [(1,), (2,)]
            mock_rect1 = MagicMock()
            mock_rect2 = MagicMock()
            # Each xref has one rect
            mock_page.get_image_rects.side_effect = [[mock_rect1], [mock_rect2]]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)

            mock_open.return_value = mock_doc

            phase.execute(mock_state)

        # Should draw rectangle for each image
        assert mock_page.draw_rect.call_count == 2

    def test__should_handle_multiple_pages(self, mock_state, tmp_path):
        """Test processing multiple pages with images."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=2)

            # Page 1 with 1 image
            mock_page1 = MagicMock()
            mock_page1.get_images.return_value = [(1,)]
            mock_page1.get_image_rects.return_value = [MagicMock()]

            # Page 2 with 2 images
            mock_page2 = MagicMock()
            mock_page2.get_images.return_value = [(2,), (3,)]
            mock_page2.get_image_rects.side_effect = [[MagicMock()], [MagicMock()]]

            def get_page(idx):
                return [mock_page1, mock_page2][idx]

            mock_doc.__getitem__ = MagicMock(side_effect=get_page)

            mock_open.return_value = mock_doc

            phase.execute(mock_state)

        # Page 1: 1 image
        assert mock_page1.draw_rect.call_count == 1
        # Page 2: 2 images
        assert mock_page2.draw_rect.call_count == 2

    def test__should_handle_pdf_with_no_images(self, mock_state, tmp_path):
        """Test handling of PDF without any images."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=3)

            mock_page = MagicMock()
            mock_page.get_images.return_value = []
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)

            mock_open.return_value = mock_doc

            result = phase.execute(mock_state)

        assert result.status == PhaseStatus.SUCCESS
        # No draw_rect calls since no images
        mock_page.draw_rect.assert_not_called()

    def test__should_return_error__when_pdf_open_fails(self, mock_state):
        """Test error handling when PDF cannot be opened."""
        phase = Phase2()

        with patch("fitz.open", side_effect=Exception("File not found")):
            result = phase.execute(mock_state)

        assert result.status == PhaseStatus.ERROR
        assert "File not found" in result.errors[0]

    def test__should_return_error__when_image_covering_fails(self, mock_state):
        """Test error handling when drawing rectangle fails."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)

            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.get_image_rects.return_value = [MagicMock()]
            mock_page.draw_rect.side_effect = Exception("Drawing failed")
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)

            mock_open.return_value = mock_doc

            result = phase.execute(mock_state)

        assert result.status == PhaseStatus.ERROR
        assert "Drawing failed" in result.errors[0]

    def test__should_report_step_results__when_successful(self, mock_state, tmp_path):
        """Test that step results are properly reported on success."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=2)

            # Each page has 1 image
            mock_page = MagicMock()
            mock_page.get_images.return_value = [(1,)]
            mock_page.get_image_rects.return_value = [MagicMock()]
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)

            mock_open.return_value = mock_doc

            result = phase.execute(mock_state)

        # Check step 2.1
        step_2_1 = [s for s in result.steps if s.step_id == "2.1"]
        assert len(step_2_1) == 1
        assert step_2_1[0].status == PhaseStatus.SUCCESS
        assert (
            step_2_1[0].message and "2" in step_2_1[0].message
        )  # 2 image instances (1 per page × 2 pages)

        # Check step 2.2
        step_2_2 = [s for s in result.steps if s.step_id == "2.2"]
        assert len(step_2_2) == 1
        assert step_2_2[0].status == PhaseStatus.SUCCESS
        assert step_2_2[0].message and "test-no-images.pdf" in step_2_2[0].message

    def test__should_set_output_file_in_result(self, mock_state, tmp_path):
        """Test that output file path is set in result."""
        phase = Phase2()

        with patch("fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=1)
            mock_doc.__getitem__ = MagicMock(
                return_value=MagicMock(get_images=MagicMock(return_value=[]))
            )
            mock_open.return_value = mock_doc

            result = phase.execute(mock_state)

        expected_path = str(tmp_path / "preprocessed" / "test-no-images.pdf")
        assert result.output_file == expected_path
