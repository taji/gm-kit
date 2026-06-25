from __future__ import annotations

from gm_kit.pdf_convert.prep.contracts import AnnotationProposal
from gm_kit.pdf_convert.prep.handlers import (
    build_annotation_proposals,
    build_resolved_guidance,
)

TABLE_BBOX = [72.0, 240.0, 520.0, 610.0]
CALLOUT_BBOX = [72.0, 80.0, 300.0, 220.0]
FULL_PAGE_BBOX = [0.0, 0.0, 612.0, 792.0]


def test_build_annotation_proposals__should_generate_deterministic_ids_and_skip_modes__when_inputs_are_valid() -> None:
    chunk_plan = {
        "chunks": [
            {
                "source_section_id": "chapter-1",
                "start_page": 1,
                "end_page": 8,
                "chunk_kind": "chapter",
                "ordinal": 1,
            },
            {
                "source_section_id": "appendix-a",
                "start_page": 9,
                "end_page": 9,
                "chunk_kind": "appendix",
                "ordinal": 2,
            },
            {
                "source_section_id": "appendix-b",
                "start_page": 10,
                "end_page": 10,
                "chunk_kind": "appendix",
                "ordinal": 3,
            },
        ]
    }

    first = build_annotation_proposals(
        page_count=10,
        images_total_count=2,
        chunk_plan=chunk_plan,
    )
    second = build_annotation_proposals(
        page_count=10,
        images_total_count=2,
        chunk_plan=chunk_plan,
    )

    assert first == second
    assert [proposal.proposal_id for proposal in first] == sorted(
        proposal.proposal_id for proposal in first
    )
    assert {proposal.label for proposal in first} == {"callout", "skip", "table"}

    full_page_skips = [
        proposal
        for proposal in first
        if proposal.label == "skip" and proposal.metadata.get("scope") == "full-page"
    ]
    assert [(proposal.page, proposal.bbox) for proposal in full_page_skips] == [
        (9, FULL_PAGE_BBOX),
        (10, FULL_PAGE_BBOX),
    ]


def test_build_annotation_proposals__should_emit_stable_table_and_callout_content__when_chunk_plan_and_images_exist() -> None:
    proposals = build_annotation_proposals(
        page_count=4,
        images_total_count=2,
        chunk_plan={
            "chunks": [
                {
                    "source_section_id": "s1",
                    "start_page": 1,
                    "end_page": 2,
                    "chunk_kind": "chapter",
                    "ordinal": 1,
                },
                {
                    "source_section_id": "s2",
                    "start_page": 3,
                    "end_page": 4,
                    "chunk_kind": "chapter",
                    "ordinal": 2,
                },
            ]
        },
    )

    table_proposals = sorted(
        (proposal for proposal in proposals if proposal.label == "table"),
        key=lambda proposal: proposal.page,
    )
    callout_proposals = sorted(
        (proposal for proposal in proposals if proposal.label == "callout"),
        key=lambda proposal: proposal.page,
    )

    assert [(proposal.page, proposal.bbox) for proposal in table_proposals] == [
        (1, TABLE_BBOX),
        (3, TABLE_BBOX),
    ]
    assert [proposal.metadata for proposal in table_proposals] == [
        {
            "chunk_kind": "chapter",
            "ordinal": 1,
            "source": "code",
            "source_section_id": "s1",
        },
        {
            "chunk_kind": "chapter",
            "ordinal": 2,
            "source": "code",
            "source_section_id": "s2",
        },
    ]
    assert [(proposal.page, proposal.bbox) for proposal in callout_proposals] == [
        (1, CALLOUT_BBOX),
        (2, CALLOUT_BBOX),
    ]
    assert all(proposal.metadata == {"source": "code", "trigger": "image-heavy-page"} for proposal in callout_proposals)


def test_build_annotation_proposals__should_generate_distinct_ids__when_stable_metadata_differs() -> None:
    proposals = build_annotation_proposals(
        page_count=4,
        images_total_count=0,
        chunk_plan={
            "chunks": [
                {
                    "source_section_id": "chapter-a",
                    "start_page": 1,
                    "end_page": 2,
                    "chunk_kind": "chapter",
                    "ordinal": 1,
                },
                {
                    "source_section_id": "chapter-b",
                    "start_page": 1,
                    "end_page": 2,
                    "chunk_kind": "chapter",
                    "ordinal": 2,
                },
            ]
        },
    )

    table_proposals = [proposal for proposal in proposals if proposal.label == "table"]

    assert len(table_proposals) == 2
    assert table_proposals[0].proposal_id != table_proposals[1].proposal_id


def test_build_annotation_proposals__should_not_emit_skip_proposals__when_trailing_single_page_chunks_are_not_appendices() -> None:
    proposals = build_annotation_proposals(
        page_count=10,
        images_total_count=0,
        chunk_plan={
            "chunks": [
                {
                    "source_section_id": "chapter-1",
                    "start_page": 1,
                    "end_page": 8,
                    "chunk_kind": "chapter",
                    "ordinal": 1,
                },
                {
                    "source_section_id": "chapter-2",
                    "start_page": 9,
                    "end_page": 9,
                    "chunk_kind": "chapter",
                    "ordinal": 2,
                },
                {
                    "source_section_id": "chapter-3",
                    "start_page": 10,
                    "end_page": 10,
                    "chunk_kind": "chapter",
                    "ordinal": 3,
                },
            ]
        },
    )

    assert all(proposal.label != "skip" for proposal in proposals)



def test_build_resolved_guidance__should_normalize_skip_table_and_callout_targets__when_given_unsorted_proposals() -> None:
    proposals = build_annotation_proposals(
        page_count=10,
        images_total_count=2,
        chunk_plan={
            "chunks": [
                {
                    "source_section_id": "appendix-a",
                    "start_page": 10,
                    "end_page": 10,
                    "chunk_kind": "appendix",
                    "ordinal": 3,
                },
                {
                    "source_section_id": "chapter-1",
                    "start_page": 1,
                    "end_page": 8,
                    "chunk_kind": "chapter",
                    "ordinal": 1,
                },
                {
                    "source_section_id": "appendix-b",
                    "start_page": 9,
                    "end_page": 9,
                    "chunk_kind": "appendix",
                    "ordinal": 2,
                },
            ]
        },
    )

    resolved = build_resolved_guidance(list(reversed(proposals)))

    assert resolved.skip_pages == [9, 10]
    assert resolved.skip_regions == []
    assert resolved.table_regions == [
        {
            "page": 1,
            "bbox": TABLE_BBOX,
            "proposal_id": next(
                proposal.proposal_id
                for proposal in proposals
                if proposal.label == "table" and proposal.page == 1
            ),
        },
        {
            "page": 9,
            "bbox": TABLE_BBOX,
            "proposal_id": next(
                proposal.proposal_id
                for proposal in proposals
                if proposal.label == "table" and proposal.page == 9
            ),
        },
        {
            "page": 10,
            "bbox": TABLE_BBOX,
            "proposal_id": next(
                proposal.proposal_id
                for proposal in proposals
                if proposal.label == "table" and proposal.page == 10
            ),
        },
    ]
    assert resolved.callout_regions == [
        {
            "page": 1,
            "bbox": CALLOUT_BBOX,
            "proposal_id": next(
                proposal.proposal_id
                for proposal in proposals
                if proposal.label == "callout" and proposal.page == 1
            ),
            "label": "callout_gm",
        },
        {
            "page": 2,
            "bbox": CALLOUT_BBOX,
            "proposal_id": next(
                proposal.proposal_id
                for proposal in proposals
                if proposal.label == "callout" and proposal.page == 2
            ),
            "label": "callout_gm",
        },
    ]



def test_build_resolved_guidance__should_split_full_page_and_region_skip_targets__when_skip_labels_mix_scopes() -> None:
    proposals = build_annotation_proposals(
        page_count=2,
        images_total_count=0,
        chunk_plan=None,
    )
    proposals.append(
        AnnotationProposal(
            proposal_id="manual-region-skip",
            label="skip",
            page=2,
            bbox=[10.0, 20.0, 30.0, 40.0],
            confidence=0.5,
            metadata={"source": "code", "scope": "region"},
        )
    )

    resolved = build_resolved_guidance(proposals)

    assert resolved.skip_pages == []
    assert resolved.skip_regions == [
        {
            "page": 2,
            "bbox": [10.0, 20.0, 30.0, 40.0],
            "proposal_id": "manual-region-skip",
        }
    ]
