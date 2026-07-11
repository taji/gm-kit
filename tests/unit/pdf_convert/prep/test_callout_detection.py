from __future__ import annotations

from pathlib import Path

import fitz  # type: ignore[import-untyped]

from gm_kit.pdf_convert.prep.callout_detection import (
    detect_callout_proposals,
    detect_callout_proposals_with_warnings,
)
from gm_kit.pdf_convert.prep.contracts import PrepGuidanceInput


def _write_sample_callout_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 120), "GM Note")
    page.insert_text(
        (72, 140),
        "This is a reviewable callout block with a few lines of text.",
    )
    page.insert_text((72, 155), "It should produce a bbox larger than the anchor line.")
    document.save(path)
    document.close()


def _write_multi_block_callout_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 120), "Keeper's Note:")
    page.insert_text(
        (72, 140),
        "This callout should stop before the next note block appears.",
    )
    page.insert_text((72, 220), "Keeper's Note:")
    page.insert_text(
        (72, 240),
        "This is a separate note block that should not be absorbed.",
    )
    document.save(path)
    document.close()


def _write_line_level_anchor_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(
        fitz.Rect(72, 120, 320, 200),
        "Introductory text before the note.\nGM Note\nThis is fallback content.",
        fontsize=11,
    )
    document.save(path)
    document.close()


def test_detect_callout_proposals__should_expand_bbox_from_anchor_text__when_gm_note_is_present(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_callout_pdf(pdf_path)

    proposals = detect_callout_proposals(pdf_path, PrepGuidanceInput())

    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.page == 1
    assert proposal.label == "callout"
    assert proposal.metadata["trigger"] == "text-anchor"
    assert proposal.metadata["callout_label"] == "callout_gm"
    assert proposal.bbox[0] < 72.0
    assert proposal.bbox[1] < 120.0
    assert proposal.bbox[3] > 155.0


def test_detect_callout_proposals__should_skip_detection__when_callouts_are_disabled(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_callout_pdf(pdf_path)

    proposals = detect_callout_proposals(
        pdf_path,
        PrepGuidanceInput(prefer_detect_callouts=False),
    )

    assert proposals == []


def test_detect_callout_proposals__should_use_phrase_only_fallback__when_anchor_phrase_is_not_first_in_a_text_block(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "line-level-anchor.pdf"
    _write_line_level_anchor_pdf(pdf_path)

    result = detect_callout_proposals_with_warnings(pdf_path, PrepGuidanceInput())

    assert len(result.proposals) == 1
    proposal = result.proposals[0]
    assert proposal.metadata["anchor_text"] == "GM Note"
    assert result.warnings
    assert "phrase-only fallback" in result.warnings[0]


def test_detect_callout_proposals_with_warnings__should_record_refinement_hint__when_a_callout_spans_multiple_text_blocks(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_callout_pdf(pdf_path)

    result = detect_callout_proposals_with_warnings(pdf_path, PrepGuidanceInput())

    assert len(result.proposals) == 1
    assert len(result.refinement_hints) == 1
    hint = result.refinement_hints[0]
    assert hint.page == 1
    assert hint.issue == "expanded_across_multiple_text_blocks"
    assert hint.anchor_text == "GM Note"
    assert hint.collected_block_count == 2
    assert "expanded a proposal across 2 text blocks" in result.warnings[0]


def test_detect_callout_proposals__should_keep_separate_note_blocks_distinct__when_multiple_note_blocks_share_a_page() -> None:
    pdf_path = Path("tests/fixtures/pdf_convert/CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf")
    proposals = detect_callout_proposals(pdf_path, PrepGuidanceInput())

    page_19_proposals = [
        proposal
        for proposal in proposals
        if proposal.page == 19 and proposal.metadata["anchor_text"].startswith("KEEPER’S NOTE:")
    ]

    left_column = sorted(
        (proposal for proposal in page_19_proposals if proposal.bbox[0] < 200.0),
        key=lambda proposal: proposal.bbox[1],
    )
    right_column = sorted(
        (proposal for proposal in page_19_proposals if proposal.bbox[0] >= 200.0),
        key=lambda proposal: proposal.bbox[1],
    )

    assert len(page_19_proposals) == 4
    assert len(left_column) == 2
    assert len(right_column) == 2
    assert left_column[0].bbox[3] <= left_column[1].bbox[1]
    assert right_column[0].bbox[3] <= right_column[1].bbox[1]


def test_detect_callout_proposals__should_emit_multiple_proposals__when_a_page_contains_multiple_note_anchors() -> None:
    pdf_path = Path("tests/fixtures/pdf_convert/CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf")
    proposals = detect_callout_proposals(pdf_path, PrepGuidanceInput())

    page_19_proposals = [
        proposal
        for proposal in proposals
        if proposal.page == 19 and proposal.metadata["anchor_text"].startswith("KEEPER’S NOTE:")
    ]

    assert len(page_19_proposals) == 4
