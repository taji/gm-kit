from __future__ import annotations

from pathlib import Path

import fitz  # type: ignore[import-untyped]

from gm_kit.pdf_convert.prep.callout_detection import detect_callout_proposals
from gm_kit.pdf_convert.prep.contracts import PrepGuidanceInput

FIXTURE_PDF = Path(__file__).parent.parent.parent.parent / (
    "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf"
)
PLACEHOLDER_BBOX = [72.0, 80.0, 300.0, 220.0]


def test_detect_callout_proposals__should_refine_bbox_from_text_anchor__when_homebrewery_fixture_contains_gm_note() -> None:
    guidance_input = PrepGuidanceInput()

    proposals = detect_callout_proposals(FIXTURE_PDF, guidance_input)

    assert proposals
    proposal = next(
        item
        for item in proposals
        if item.page == 1 and item.metadata.get("anchor_phrase") == "gm note"
    )

    doc = fitz.open(FIXTURE_PDF)
    try:
        anchor_rect = doc[0].search_for("GM Note")[0]
    finally:
        doc.close()

    bbox = fitz.Rect(*proposal.bbox)

    assert proposal.label == "callout"
    assert proposal.metadata["trigger"] == "text-anchor"
    assert proposal.metadata["callout_label"] == "callout_gm"
    assert proposal.bbox != PLACEHOLDER_BBOX
    assert bbox.intersects(anchor_rect)
    assert bbox.y0 <= anchor_rect.y0
    assert bbox.y1 >= anchor_rect.y1
