"""Unit tests for shared prep PDF handlers."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from gm_kit.pdf_convert.metadata import PDFMetadata
from gm_kit.pdf_convert.preflight import Complexity, PreflightReport, TOCApproach
from gm_kit.pdf_convert.prep.handlers import (
    create_no_images_pdf,
    extract_images_to_artifacts,
    extract_toc_to_artifact,
    render_annotated_prep_pdf,
    write_metadata_and_preflight_artifacts,
)


def test_extract_images_to_artifacts__should_write_manifest_and_images__when_pdf_has_images(
    tmp_path: Path,
) -> None:
    """It writes extracted images plus the image manifest artifact."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    images_dir = tmp_path / "images"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1,)]
        mock_page.get_image_rects.return_value = [MagicMock(x0=1, y0=2, width=3, height=4)]
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_doc.extract_image.return_value = {"image": b"png-bytes", "ext": "png"}
        mock_open.return_value = mock_doc

        manifest_path, total_images = extract_images_to_artifacts(
            pdf_path=pdf_path,
            images_dir=images_dir,
        )

    assert total_images == 1
    assert manifest_path == images_dir / "image-manifest.json"
    assert (images_dir / "page001_img01.png").read_bytes() == b"png-bytes"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["total_count"] == 1
    assert manifest["images"] == [
        {
            "alt_text": "[Figure on page 1]",
            "filename": "page001_img01.png",
            "page": 1,
            "position": {
                "height": 4,
                "width": 3,
                "x": 1,
                "y": 2,
            },
        }
    ]


def test_extract_images_to_artifacts__should_use_source_extension__when_extracted_image_is_jpeg(
    tmp_path: Path,
) -> None:
    """It preserves the source image extension in the artifact filename."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    images_dir = tmp_path / "images"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1,)]
        mock_page.get_image_rects.return_value = [MagicMock(x0=1, y0=2, width=3, height=4)]
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_doc.extract_image.return_value = {"image": b"jpeg-bytes", "ext": "jpeg"}
        mock_open.return_value = mock_doc

        manifest_path, total_images = extract_images_to_artifacts(
            pdf_path=pdf_path,
            images_dir=images_dir,
        )

    assert total_images == 1
    assert (images_dir / "page001_img01.jpeg").read_bytes() == b"jpeg-bytes"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["images"][0]["filename"] == "page001_img01.jpeg"


def test_create_no_images_pdf__should_save_expected_output__when_pdf_is_processed(
    tmp_path: Path,
) -> None:
    """It saves the expected no-images PDF and reports removed instances."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_pdf_path = tmp_path / "sample-no-images.pdf"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_images.return_value = []
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_open.return_value = mock_doc

        images_removed = create_no_images_pdf(
            pdf_path=pdf_path,
            output_pdf_path=output_pdf_path,
    )

    assert images_removed == 0
    mock_doc.save.assert_called_once_with(output_pdf_path, garbage=4, clean=True, deflate=True)


def test_create_no_images_pdf__should_return_removed_instance_count__when_images_have_rects(
    tmp_path: Path,
) -> None:
    """It returns the number of covered image instances."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_pdf_path = tmp_path / "sample-no-images.pdf"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1,), (2,)]
        mock_page.get_image_rects.side_effect = [
            [MagicMock(), MagicMock()],
            [MagicMock()],
        ]
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_open.return_value = mock_doc

        images_removed = create_no_images_pdf(
            pdf_path=pdf_path,
            output_pdf_path=output_pdf_path,
        )

    assert images_removed == 3


def test_extract_toc_to_artifact__should_write_embedded_toc_file__when_toc_exists(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_path = tmp_path / "toc-extracted.txt"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [[1, "Introduction", 1], [2, "Maps", 3]]
        mock_open.return_value = mock_doc

        toc_entries = extract_toc_to_artifact(pdf_path=pdf_path, output_path=output_path)

    assert len(toc_entries) == 2
    assert "Introduction (page 1)" in output_path.read_text(encoding="utf-8")


def test_write_metadata_and_preflight_artifacts__should_persist_json_outputs__when_analysis_succeeds(
    tmp_path: Path,
) -> None:
    metadata = PDFMetadata(page_count=1, file_size_bytes=10)
    report = PreflightReport(
        pdf_name="sample.pdf",
        file_size_display="10 B",
        page_count=1,
        image_count=0,
        text_extractable=True,
        toc_approach=TOCApproach.NONE,
        font_complexity=Complexity.LOW,
        overall_complexity=Complexity.LOW,
    )

    write_metadata_and_preflight_artifacts(
        metadata=metadata,
        report=report,
        metadata_path=tmp_path / "metadata.json",
        preflight_report_path=tmp_path / "preflight-report.json",
    )

    assert (tmp_path / "metadata.json").exists()
    assert (tmp_path / "preflight-report.json").exists()


def test_render_annotated_prep_pdf__should_use_distinct_colors__when_tables_and_callouts_are_present(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_path = tmp_path / "annotated-prep.pdf"

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_page = MagicMock()
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)

        callout_annot = MagicMock()
        table_annot = MagicMock()
        mock_page.add_freetext_annot.side_effect = [table_annot, callout_annot]
        mock_open.return_value = mock_doc

        render_annotated_prep_pdf(
            pdf_path=pdf_path,
            proposals=[
                MagicMock(
                    page=1,
                    label="table",
                    proposal_id="ap-table",
                    bbox=[1.0, 2.0, 3.0, 4.0],
                ),
                MagicMock(
                    page=1,
                    label="callout",
                    proposal_id="ap-callout",
                    bbox=[5.0, 6.0, 7.0, 8.0],
                ),
            ],
            output_pdf_path=output_path,
        )

    assert mock_page.add_freetext_annot.call_count == 2
    fill_colors = [call.kwargs["fill_color"] for call in mock_page.add_freetext_annot.call_args_list]
    assert (0.6000000238418579, 0.7568627595901489, 0.9450980424880981) in fill_colors
    assert (1, 1, 0) in fill_colors
    mock_doc.save.assert_called_once_with(output_path, garbage=4, clean=True, deflate=True)
