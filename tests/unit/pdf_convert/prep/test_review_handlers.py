from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths
from gm_kit.pdf_convert.prep.contracts import (
    AnnotationProposal,
    AnnotationReviewEdits,
    PrepGuidanceInput,
)
from gm_kit.pdf_convert.prep.handlers import (
    apply_review_edits_to_proposals,
    build_annotation_review_edits,
    build_final_resolved_guidance,
    handle_finalize_reviewed_guidance,
    handle_seed_annotation_review,
    load_effective_prep_guidance,
    render_annotated_prep_pdf,
)


def test_build_annotation_review_edits__should_map_review_mode_to_review_status__when_review_mode_is_valid() -> None:
    interactive = build_annotation_review_edits(
        review_mode="interactive",
        skip_ranges_input="2,5,12-14",
        skip_pages_explicit=[2, 5, 12, 13, 14],
    )
    auto_accept = build_annotation_review_edits(
        review_mode="auto_accept",
        skip_ranges_input="",
        skip_pages_explicit=[],
    )
    bypass = build_annotation_review_edits(
        review_mode="bypass",
        skip_ranges_input="7",
        skip_pages_explicit=[7],
    )

    assert interactive == AnnotationReviewEdits(
        review_mode="interactive",
        review_status="pending",
        skip_ranges_input="2,5,12-14",
        skip_pages_explicit=[2, 5, 12, 13, 14],
        proposal_decisions={},
        updated_regions={},
        notes="",
    )
    assert auto_accept.review_status == "auto_accepted"
    assert bypass.review_status == "accepted"
    assert bypass.skip_ranges_input == "7"
    assert bypass.skip_pages_explicit == [7]


def test_apply_review_edits_to_proposals__should_apply_reject_and_edit_decisions__when_review_payload_is_valid() -> None:
    proposals = [
        AnnotationProposal(
            proposal_id="ap-001",
            label="table",
            page=5,
            bbox=[72.0, 240.0, 520.0, 610.0],
            confidence=0.5,
            metadata={
                "source": "code",
                "source_section_id": "s1",
                "chunk_kind": "chapter",
                "ordinal": 1,
            },
        ),
        AnnotationProposal(
            proposal_id="ap-002",
            label="callout",
            page=6,
            bbox=[72.0, 80.0, 300.0, 220.0],
            confidence=0.5,
            metadata={"source": "code", "trigger": "image-heavy-page"},
        ),
    ]
    edits = AnnotationReviewEdits(
        review_mode="interactive",
        review_status="revised",
        skip_ranges_input="",
        skip_pages_explicit=[],
        proposal_decisions={"ap-001": "edit", "ap-002": "reject"},
        updated_regions={
            "ap-001": {
                "page": 5,
                "bbox": [70.0, 230.0, 500.0, 600.0],
                "label": "table",
            }
        },
        notes="",
    )

    reviewed = apply_review_edits_to_proposals(proposals, edits)

    assert [
        (proposal.proposal_id, proposal.label, proposal.page, proposal.bbox)
        for proposal in reviewed
    ] == [("ap-001", "table", 5, [70.0, 230.0, 500.0, 600.0])]
    assert reviewed[0].confidence == 0.5
    assert reviewed[0].metadata == {
        "source": "code",
        "source_section_id": "s1",
        "chunk_kind": "chapter",
        "ordinal": 1,
    }


def test_build_final_resolved_guidance__should_apply_skip_precedence_and_merge_explicit_pages__when_skip_overlaps_table_region() -> None:
    proposals = [
        AnnotationProposal(
            proposal_id="ap-explicit-table",
            label="table",
            page=2,
            bbox=[72.0, 240.0, 520.0, 610.0],
            confidence=0.5,
            metadata={"source": "code", "source_section_id": "s0", "chunk_kind": "chapter", "ordinal": 0},
        ),
        AnnotationProposal(
            proposal_id="ap-skip-full",
            label="skip",
            page=5,
            bbox=[0.0, 0.0, 612.0, 792.0],
            confidence=0.9,
            metadata={"source": "code", "scope": "full-page", "reason": "appendix"},
        ),
        AnnotationProposal(
            proposal_id="ap-skip-region",
            label="skip",
            page=6,
            bbox=[200.0, 200.0, 300.0, 300.0],
            confidence=0.9,
            metadata={"source": "code", "scope": "region", "reason": "cover-art"},
        ),
        AnnotationProposal(
            proposal_id="ap-table-overlap",
            label="table",
            page=6,
            bbox=[150.0, 150.0, 350.0, 350.0],
            confidence=0.5,
            metadata={"source": "code", "source_section_id": "s1", "chunk_kind": "chapter", "ordinal": 1},
        ),
        AnnotationProposal(
            proposal_id="ap-callout-keep",
            label="callout",
            page=6,
            bbox=[20.0, 20.0, 80.0, 80.0],
            confidence=0.5,
            metadata={"source": "code", "trigger": "image-heavy-page"},
        ),
    ]

    resolved = build_final_resolved_guidance(
        proposals=proposals,
        skip_pages_explicit=[2],
        review_mode="interactive",
        review_status="accepted",
        skip_ranges_input="2,5",
    )

    assert resolved.skip_pages == [2, 5]
    assert resolved.skip_regions == [
        {
            "page": 6,
            "bbox": [200.0, 200.0, 300.0, 300.0],
            "proposal_id": "ap-skip-region",
        }
    ]
    assert resolved.table_regions == []
    assert resolved.callout_regions == [
        {
            "page": 6,
            "bbox": [20.0, 20.0, 80.0, 80.0],
            "proposal_id": "ap-callout-keep",
            "label": "callout_gm",
        }
    ]
def test_render_annotated_prep_pdf__should_draw_rectangles_and_stamp_labels__when_pdf_is_renderable(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_pdf_path = tmp_path / "annotated.pdf"
    proposals = [
        AnnotationProposal(
            proposal_id="ap-002",
            label="callout",
            page=2,
            bbox=[10.0, 20.0, 50.0, 60.0],
            confidence=0.5,
            metadata={"source": "code", "trigger": "image-heavy-page"},
        ),
        AnnotationProposal(
            proposal_id="ap-001",
            label="table",
            page=1,
            bbox=[72.0, 240.0, 520.0, 610.0],
            confidence=0.5,
            metadata={
                "source": "code",
                "source_section_id": "s1",
                "chunk_kind": "chapter",
                "ordinal": 1,
            },
        ),
    ]

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=2)
        first_page = MagicMock()
        second_page = MagicMock()
        mock_doc.__getitem__ = MagicMock(side_effect=[first_page, second_page])
        mock_open.return_value = mock_doc

        render_annotated_prep_pdf(
            pdf_path=pdf_path,
            proposals=proposals,
            output_pdf_path=output_pdf_path,
        )

    first_page.draw_rect.assert_called_once()
    first_page.insert_text.assert_called_once()
    second_page.draw_rect.assert_called_once()
    second_page.insert_text.assert_called_once()
    assert first_page.insert_text.call_args.args[1] == "ap-001 table"
    assert second_page.insert_text.call_args.args[1] == "ap-002 callout"
    mock_doc.save.assert_called_once()


def test_render_annotated_prep_pdf__should_not_raise__when_pdf_cannot_be_opened(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_pdf_path = tmp_path / "annotated.pdf"

    with patch("fitz.open", side_effect=RuntimeError("boom")):
        render_annotated_prep_pdf(
            pdf_path=pdf_path,
            proposals=[],
            output_pdf_path=output_pdf_path,
        )

    assert not output_pdf_path.exists()


def test_render_annotated_prep_pdf__should_not_raise__when_pdf_cannot_be_saved(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_text("%PDF-1.7\n", encoding="utf-8")
    output_pdf_path = tmp_path / "annotated.pdf"
    proposal = AnnotationProposal(
        proposal_id="ap-001",
        label="table",
        page=1,
        bbox=[72.0, 240.0, 520.0, 610.0],
        confidence=0.5,
        metadata={
            "source": "code",
            "source_section_id": "s1",
            "chunk_kind": "chapter",
            "ordinal": 1,
        },
    )

    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        first_page = MagicMock()
        mock_doc.__getitem__ = MagicMock(return_value=first_page)
        mock_doc.save.side_effect = RuntimeError("boom")
        mock_open.return_value = mock_doc

        render_annotated_prep_pdf(
            pdf_path=pdf_path,
            proposals=[proposal],
            output_pdf_path=output_pdf_path,
        )

    first_page.draw_rect.assert_called_once()
    first_page.insert_text.assert_called_once()
    mock_doc.save.assert_called_once()
    assert not output_pdf_path.exists()


def test_handle_finalize_reviewed_guidance__should_merge_skip_ranges_and_review_edits__when_review_artifacts_exist(
    tmp_path: Path,
) -> None:
    workspace_dir = tmp_path / "workspace"
    analysis_paths = build_analysis_artifact_paths(workspace_dir, pdf_stem="sample")
    for artifact_path in [
        analysis_paths.metadata,
        analysis_paths.guidance_defaults,
        analysis_paths.annotation_proposals,
        analysis_paths.annotation_review_edits,
    ]:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_paths.metadata.write_text(json.dumps({"page_count": 12}) + "\n", encoding="utf-8")
    analysis_paths.guidance_defaults.write_text(
        json.dumps(PrepGuidanceInput().to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    analysis_paths.annotation_proposals.write_text(
        json.dumps(
            [
                {
                    "proposal_id": "ap-001",
                    "label": "table",
                    "page": 2,
                    "bbox": [72.0, 240.0, 520.0, 610.0],
                    "confidence": 0.5,
                    "metadata": {
                        "source": "code",
                        "source_section_id": "s1",
                        "chunk_kind": "chapter",
                        "ordinal": 1,
                    },
                },
                {
                    "proposal_id": "ap-002",
                    "label": "callout",
                    "page": 7,
                    "bbox": [72.0, 80.0, 300.0, 220.0],
                    "confidence": 0.5,
                    "metadata": {"source": "code", "trigger": "image-heavy-page"},
                },
                {
                    "proposal_id": "ap-003",
                    "label": "skip",
                    "page": 6,
                    "bbox": [0.0, 0.0, 612.0, 792.0],
                    "confidence": 0.9,
                    "metadata": {"source": "code", "scope": "full-page"},
                },
            ],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    analysis_paths.annotation_review_edits.write_text(
        json.dumps(
            {
                "review_mode": "interactive",
                "review_status": "revised",
                "skip_ranges_input": "2-3",
                "skip_pages_explicit": [5],
                "proposal_decisions": {"ap-001": "accept", "ap-002": "accept", "ap-003": "accept"},
                "updated_regions": {},
                "notes": "",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    handle_finalize_reviewed_guidance(analysis_paths=analysis_paths)

    resolved_payload = json.loads(
        analysis_paths.reviewed_guidance.read_text(encoding="utf-8")
    )

    assert resolved_payload["skip_pages"] == [2, 3, 5, 6]
    assert resolved_payload["table_regions"] == []
    assert resolved_payload["callout_regions"] == [
        {
            "page": 7,
            "bbox": [72.0, 80.0, 300.0, 220.0],
            "proposal_id": "ap-002",
            "label": "callout_gm",
        }
    ]


def test_load_effective_prep_guidance__should_prefer_reviewed_artifact__when_reviewed_exists(
    tmp_path: Path,
) -> None:
    workspace_dir = tmp_path / "workspace"
    analysis_paths = build_analysis_artifact_paths(workspace_dir, pdf_stem="sample")
    analysis_paths.guidance_resolved.parent.mkdir(parents=True, exist_ok=True)
    analysis_paths.guidance_resolved.write_text(
        json.dumps(
            {
                "skip_pages": [],
                "skip_regions": [],
                "table_regions": [],
                "callout_regions": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    analysis_paths.reviewed_guidance.write_text(
        json.dumps(
            {
                "skip_pages": [2],
                "skip_regions": [],
                "table_regions": [],
                "callout_regions": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    loaded = load_effective_prep_guidance(analysis_paths)

    assert loaded.skip_pages == [2]


def test_handle_seed_annotation_review__should_seed_auto_accept_state__when_auto_proceed_is_true(
    tmp_path: Path,
) -> None:
    workspace_dir = tmp_path / "workspace"
    analysis_paths = build_analysis_artifact_paths(workspace_dir, pdf_stem="sample")
    analysis_paths.guidance_defaults.parent.mkdir(parents=True, exist_ok=True)
    analysis_paths.guidance_defaults.write_text(
        json.dumps(
            PrepGuidanceInput(auto_accept_annotations=False, review_requested=True).to_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    handle_seed_annotation_review(
        analysis_paths=analysis_paths,
        auto_proceed=True,
    )

    review_payload = json.loads(
        analysis_paths.annotation_review_edits.read_text(encoding="utf-8")
    )

    assert review_payload["review_mode"] == "auto_accept"
    assert review_payload["review_status"] == "auto_accepted"
