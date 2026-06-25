"""Unit tests for Phase 3 (TOC & Font Extraction)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase3 import Phase3
from gm_kit.pdf_convert.state import ConversionState


class TestPhase3Execute:
    def test__should_use_shared_toc_helper__when_embedded_toc_exists(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        phase = Phase3()

        toc_path = tmp_path / "toc-extracted.txt"
        toc_path.write_text("# TOC Source: embedded\n", encoding="utf-8")

        with (
            patch("gm_kit.pdf_convert.phases.phase3.fitz.open") as mock_open,
            patch(
                "gm_kit.pdf_convert.phases.phase3.extract_toc_to_artifact",
                return_value=[{"level": 1, "title": "Introduction", "page": 1}],
            ) as mock_extract,
        ):
            mock_doc = MagicMock()
            mock_doc.get_toc.return_value = [[1, "Introduction", 1]]
            mock_open.return_value = mock_doc

            phase._extract_toc(pdf_path=pdf_path, output_dir=tmp_path, result=phase.create_result())

        mock_extract.assert_called_once_with(pdf_path=pdf_path, output_path=toc_path)

    def test__should_report_success__when_embedded_toc_exists(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
        phase = Phase3()

        with (
            patch("gm_kit.pdf_convert.phases.phase3.fitz.open") as mock_open,
            patch(
                "gm_kit.pdf_convert.phases.phase3.extract_toc_to_artifact",
                return_value=[{"level": 1, "title": "Introduction", "page": 1}],
            ),
        ):
            mock_doc = MagicMock()
            mock_doc.get_toc.return_value = [[1, "Introduction", 1]]
            mock_open.return_value = mock_doc

            result = phase.execute(state)

        assert result.status in {PhaseStatus.SUCCESS, PhaseStatus.WARNING}
