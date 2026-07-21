from __future__ import annotations

from pathlib import Path

import fitz  # type: ignore[import-untyped]

from gm_kit.pdf_convert.prep.contracts import PrepGuidanceInput
from gm_kit.pdf_convert.prep.handlers import build_annotation_proposals

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent.parent / "tests/fixtures/pdf_convert"
HOMEBREWERY_FIXTURE = FIXTURE_DIR / "The Homebrewery - NaturalCrit-TablesAnnotatedByTodd.pdf"
COFC_FIXTURE = FIXTURE_DIR / "CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules-TablesAnnotatedByTodd.pdf"


def _load_table_proposals(pdf_path: Path):
    doc = fitz.open(pdf_path)
    try:
        return [
            proposal
            for proposal in build_annotation_proposals(
                pdf_path=pdf_path,
                page_count=len(doc),
                images_total_count=0,
                chunk_plan=None,
                guidance_input=PrepGuidanceInput(),
            )
            if proposal.label == "table"
        ]
    finally:
        doc.close()


def _load_annotated_table_rects(pdf_path: Path) -> list[tuple[int, fitz.Rect]]:
    doc = fitz.open(pdf_path)
    try:
        rects: list[tuple[int, fitz.Rect]] = []
        for page_index in range(len(doc)):
            page = doc[page_index]
            for annot in page.annots() or []:
                if annot.info.get("content", "").startswith("table"):
                    rects.append((page_index + 1, annot.rect))
        return rects
    finally:
        doc.close()


def test_table_detection_rules__should_find_only_homebrewery_table__when_using_annotated_fixture() -> None:
    proposals = _load_table_proposals(HOMEBREWERY_FIXTURE)
    annotated_rects = _load_annotated_table_rects(HOMEBREWERY_FIXTURE)

    assert len(proposals) == 1
    assert len(annotated_rects) == 1

    proposal = proposals[0]
    page_number, annotated_rect = annotated_rects[0]
    proposal_rect = fitz.Rect(*proposal.bbox)

    assert proposal.page == page_number == 2
    assert proposal_rect.intersects(annotated_rect)


def test_table_detection_rules__should_find_only_expected_cofc_tables__when_using_annotated_fixture() -> None:
    proposals = _load_table_proposals(COFC_FIXTURE)
    annotated_rects = _load_annotated_table_rects(COFC_FIXTURE)

    assert len(proposals) == 3
    assert len(annotated_rects) == 3

    proposal_pages = sorted(proposal.page for proposal in proposals)
    annotated_pages = sorted(page for page, _ in annotated_rects)

    assert proposal_pages == annotated_pages == [16, 29, 31]

    for proposal in proposals:
        proposal_rect = fitz.Rect(*proposal.bbox)
        matching_rect = next(rect for page, rect in annotated_rects if page == proposal.page)
        assert proposal_rect.intersects(matching_rect)

    page_16_proposal = next(proposal for proposal in proposals if proposal.page == 16)
    assert "Severe" in page_16_proposal.metadata["table_text"]
    assert "Splat" in page_16_proposal.metadata["table_text"]
