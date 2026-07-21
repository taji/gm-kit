from __future__ import annotations

import json
from pathlib import Path

import fitz  # type: ignore[import-untyped]
from PIL import Image

from gm_kit.pdf_convert.prep.callout_detection import CalloutRefinementHint
from gm_kit.pdf_convert.prep.contracts import AnnotationProposal, PrepGuidanceInput
from gm_kit.pdf_convert.prep.refinement import (
    MockCalloutRefinementAgent,
    build_callout_refinement_agent,
    build_callout_refinement_inputs,
    build_table_refinement_inputs,
    refine_callout_proposals,
)


def _write_callout_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=300, height=220)
    page.draw_rect(
        fitz.Rect(40, 40, 260, 150),
        color=(0.1, 0.5, 0.1),
        fill=(0.1, 0.75, 0.1),
        width=1,
    )
    page.insert_text((55, 65), "GM Note", fontsize=12)
    page.insert_text((55, 90), "Line one of the note.", fontsize=11)
    page.insert_text((55, 112), "Line two of the note.", fontsize=11)
    document.save(path)
    document.close()


def _write_table_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=320, height=260)
    page.insert_text((40, 48), "Weapons Table", fontsize=12)
    page.insert_text((40, 76), "Name", fontsize=10)
    page.insert_text((150, 76), "Damage", fontsize=10)
    page.insert_text((40, 102), "Sword", fontsize=10)
    page.insert_text((150, 102), "1d8", fontsize=10)
    document.save(path)
    document.close()


def test_build_callout_refinement_inputs__should_render_source_pdf_crop__when_hint_marks_multiblock_callout(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    _write_callout_pdf(pdf_path)

    proposal = AnnotationProposal(
        proposal_id="ap-test-refine",
        label="callout",
        page=1,
        bbox=[40.0, 40.0, 260.0, 150.0],
        confidence=0.88,
        metadata={
            "source": "code",
            "trigger": "text-anchor",
            "anchor_phrase": "gm note",
            "anchor_text": "GM Note",
            "callout_label": "callout_gm",
        },
    )
    hint = CalloutRefinementHint(
        proposal_id="ap-test-refine",
        page=1,
        issue="expanded_across_multiple_text_blocks",
        anchor_phrase="gm note",
        anchor_text="GM Note",
        collected_block_count=3,
    )

    entries = build_callout_refinement_inputs(
        pdf_path=pdf_path,
        proposals=[proposal],
        refinement_hints=[hint],
        guidance_input=PrepGuidanceInput(),
        manifest_path=tmp_path / "annotation-refinement-inputs.json",
        crops_dir=tmp_path / "annotation-refinement-crops",
    )

    manifest = json.loads((tmp_path / "annotation-refinement-inputs.json").read_text(encoding="utf-8"))
    crop_path = tmp_path / "annotation-refinement-crops" / "callout-ap-test-refine_p001.png"
    with Image.open(crop_path) as image:
        sampled_pixel = image.getpixel((20, 20))

    assert len(entries) == 1
    assert manifest["candidate_count"] == 1
    assert manifest["items"][0]["proposal_id"] == "ap-test-refine"
    assert Path(manifest["items"][0]["image_path"]) == crop_path
    assert manifest["items"][0]["crop_rect"] == [34.0, 36.0, 266.0, 156.0]
    assert crop_path.exists()
    assert sampled_pixel[1] > sampled_pixel[0]
    assert sampled_pixel[1] > sampled_pixel[2]


def test_build_callout_refinement_inputs__should_write_empty_manifest__when_no_hints_are_flagged(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    _write_callout_pdf(pdf_path)

    proposal = AnnotationProposal(
        proposal_id="ap-test-refine",
        label="callout",
        page=1,
        bbox=[40.0, 40.0, 260.0, 150.0],
        confidence=0.88,
        metadata={
            "source": "code",
            "trigger": "text-anchor",
            "anchor_phrase": "gm note",
            "anchor_text": "GM Note",
            "callout_label": "callout_gm",
        },
    )

    build_callout_refinement_inputs(
        pdf_path=pdf_path,
        proposals=[proposal],
        refinement_hints=[],
        guidance_input=PrepGuidanceInput(),
        manifest_path=tmp_path / "annotation-refinement-inputs.json",
        crops_dir=tmp_path / "annotation-refinement-crops",
    )

    manifest = json.loads((tmp_path / "annotation-refinement-inputs.json").read_text(encoding="utf-8"))
    crops_dir = tmp_path / "annotation-refinement-crops"

    assert manifest["candidate_count"] == 0
    assert manifest["items"] == []
    assert list(crops_dir.glob("*.png")) == []


def test_build_table_refinement_inputs__should_render_source_pdf_crop__when_table_proposal_exists(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    _write_table_pdf(pdf_path)

    proposal = AnnotationProposal(
        proposal_id="ap-table-refine",
        label="table",
        page=1,
        bbox=[40.0, 40.0, 200.0, 120.0],
        confidence=0.75,
        metadata={
            "source": "code",
            "trigger": "text-pattern",
            "table_title": "Weapons Table",
            "table_text": "Weapons Table Name Damage Sword 1d8",
        },
    )

    entries = build_table_refinement_inputs(
        pdf_path=pdf_path,
        proposals=[proposal],
        guidance_input=PrepGuidanceInput(),
        manifest_path=tmp_path / "annotation-table-refinement-inputs.json",
        crops_dir=tmp_path / "annotation-refinement-crops",
    )

    manifest = json.loads(
        (tmp_path / "annotation-table-refinement-inputs.json").read_text(encoding="utf-8")
    )
    crop_path = tmp_path / "annotation-refinement-crops" / "table-ap-table-refine_p001.png"

    assert len(entries) == 1
    assert manifest["candidate_count"] == 1
    assert manifest["items"][0]["proposal_id"] == "ap-table-refine"
    assert Path(manifest["items"][0]["image_path"]) == crop_path
    assert manifest["items"][0]["crop_rect"][2] - manifest["items"][0]["crop_rect"][0] >= 160.0
    assert manifest["items"][0]["crop_rect"][3] - manifest["items"][0]["crop_rect"][1] >= 120.0
    assert crop_path.exists()


def test_refine_callout_proposals__should_tighten_bbox__when_source_crop_has_visible_content(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    _write_callout_pdf(pdf_path)

    proposal = AnnotationProposal(
        proposal_id="ap-test-refine",
        label="callout",
        page=1,
        bbox=[40.0, 40.0, 260.0, 150.0],
        confidence=0.88,
        metadata={
            "source": "code",
            "trigger": "text-anchor",
            "anchor_phrase": "gm note",
            "anchor_text": "GM Note",
            "callout_label": "callout_gm",
        },
    )
    hint = CalloutRefinementHint(
        proposal_id="ap-test-refine",
        page=1,
        issue="expanded_across_multiple_text_blocks",
        anchor_phrase="gm note",
        anchor_text="GM Note",
        collected_block_count=3,
    )
    entries = build_callout_refinement_inputs(
        pdf_path=pdf_path,
        proposals=[proposal],
        refinement_hints=[hint],
        guidance_input=PrepGuidanceInput(),
        manifest_path=tmp_path / "annotation-refinement-inputs.json",
        crops_dir=tmp_path / "annotation-refinement-crops",
    )

    refined_proposals, decisions = refine_callout_proposals(
        proposals=[proposal],
        crop_entries=entries,
    )

    assert len(decisions) == 1
    assert decisions[0].action == "refine"
    assert refined_proposals[0].bbox != proposal.bbox
    assert refined_proposals[0].bbox[0] >= proposal.bbox[0] - 2.0
    assert refined_proposals[0].bbox[1] >= proposal.bbox[1] - 2.0
    assert refined_proposals[0].bbox[2] <= proposal.bbox[2] + 2.0
    assert refined_proposals[0].bbox[3] <= proposal.bbox[3] + 2.0


def test_refine_callout_proposals__should_leave_bbox_unchanged__when_skip_flag_is_set(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    _write_callout_pdf(pdf_path)

    proposal = AnnotationProposal(
        proposal_id="ap-test-refine",
        label="callout",
        page=1,
        bbox=[40.0, 40.0, 260.0, 150.0],
        confidence=0.88,
        metadata={
            "source": "code",
            "trigger": "text-anchor",
            "anchor_phrase": "gm note",
            "anchor_text": "GM Note",
            "callout_label": "callout_gm",
        },
    )
    hint = CalloutRefinementHint(
        proposal_id="ap-test-refine",
        page=1,
        issue="expanded_across_multiple_text_blocks",
        anchor_phrase="gm note",
        anchor_text="GM Note",
        collected_block_count=3,
    )
    entries = build_callout_refinement_inputs(
        pdf_path=pdf_path,
        proposals=[proposal],
        refinement_hints=[hint],
        guidance_input=PrepGuidanceInput(),
        manifest_path=tmp_path / "annotation-refinement-inputs.json",
        crops_dir=tmp_path / "annotation-refinement-crops",
    )

    refined_proposals, decisions = refine_callout_proposals(
        proposals=[proposal],
        crop_entries=entries,
        skip_refinement=True,
    )

    assert decisions == []
    assert refined_proposals[0].bbox == proposal.bbox


def test_build_callout_refinement_agent__should_return_none__when_mode_is_skip() -> None:
    assert build_callout_refinement_agent("skip") is None


def test_refine_callout_proposals__should_accept_an_injected_mock_agent__when_agent_is_provided(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    _write_callout_pdf(pdf_path)

    proposal = AnnotationProposal(
        proposal_id="ap-test-refine",
        label="callout",
        page=1,
        bbox=[40.0, 40.0, 260.0, 150.0],
        confidence=0.88,
        metadata={
            "source": "code",
            "trigger": "text-anchor",
            "anchor_phrase": "gm note",
            "anchor_text": "GM Note",
            "callout_label": "callout_gm",
        },
    )
    hint = CalloutRefinementHint(
        proposal_id="ap-test-refine",
        page=1,
        issue="expanded_across_multiple_text_blocks",
        anchor_phrase="gm note",
        anchor_text="GM Note",
        collected_block_count=3,
    )
    entries = build_callout_refinement_inputs(
        pdf_path=pdf_path,
        proposals=[proposal],
        refinement_hints=[hint],
        guidance_input=PrepGuidanceInput(),
        manifest_path=tmp_path / "annotation-refinement-inputs.json",
        crops_dir=tmp_path / "annotation-refinement-crops",
    )

    refined_proposals, decisions = refine_callout_proposals(
        proposals=[proposal],
        crop_entries=entries,
        agent=MockCalloutRefinementAgent(),
    )

    assert len(decisions) == 1
    assert refined_proposals[0].bbox != proposal.bbox
