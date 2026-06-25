import pytest

from gm_kit.pdf_convert.prep.contracts import (
    AnnotationProposal,
    PrepGuidanceInput,
    PrepGuidanceResolved,
)


def test_annotation_proposal__should_roundtrip_shared_base_schema__when_valid_payload_is_used() -> None:
    proposal = AnnotationProposal(
        proposal_id="p-001",
        label="table",
        page=18,
        bbox=[72.0, 240.0, 520.0, 610.0],
        confidence=0.88,
        metadata={"source": "code", "rows_estimate": 12},
    )

    payload = proposal.to_dict()
    restored = AnnotationProposal.from_dict(payload)

    assert restored == proposal


def test_annotation_proposal__should_preserve_json_safe_metadata__when_nested_payload_is_used() -> None:
    proposal = AnnotationProposal(
        proposal_id="p-002",
        label="callout",
        page=7,
        bbox=[10.0, 20.0, 30.0, 40.0],
        confidence=0.42,
        metadata={
            "source": "hybrid",
            "signals": {"detectors": ["ocr", "layout"], "score": 0.9},
        },
    )

    payload = proposal.to_dict()

    assert payload["metadata"] == {
        "source": "hybrid",
        "signals": {"detectors": ["ocr", "layout"], "score": 0.9},
    }


def test_prep_guidance_resolved__should_roundtrip_skip_page_and_region_data__when_valid_payload_is_used() -> None:
    resolved = PrepGuidanceResolved(
        skip_pages=[12],
        skip_regions=[{"page": 18, "bbox": [10.0, 10.0, 20.0, 20.0]}],
        table_regions=[{"page": 20, "bbox": [30.0, 30.0, 40.0, 40.0]}],
        callout_regions=[
            {
                "page": 21,
                "bbox": [50.0, 50.0, 60.0, 60.0],
                "proposal_id": "ap-001",
                "label": "callout_gm",
                "metadata": {"source": "code", "notes": ["reviewed"]},
            }
        ],
    )

    payload = resolved.to_dict()
    restored = PrepGuidanceResolved.from_dict(payload)

    assert restored == resolved


def test_prep_guidance_resolved__should_preserve_callout_labels_and_metadata__when_valid_payload_is_used() -> None:
    payload = {
        "skip_pages": [],
        "skip_regions": [],
        "table_regions": [],
        "callout_regions": [
            {
                "page": 3,
                "bbox": [10.0, 20.0, 30.0, 40.0],
                "proposal_id": "ap-007",
                "label": "callout_read_aloud",
                "metadata": {"source": "code", "confidence": 0.9},
            }
        ],
    }

    restored = PrepGuidanceResolved.from_dict(payload)

    assert restored.to_dict() == payload


def test_prep_guidance_input__should_preserve_user_preferences__when_valid_payload_is_used() -> None:
    guidance = PrepGuidanceInput(
        prefer_detect_tables=True,
        prefer_detect_callouts=False,
        prefer_skip_full_page_artifacts=True,
    )

    payload = guidance.to_dict()
    restored = PrepGuidanceInput.from_dict(payload)

    assert restored == guidance


def test_annotation_proposal__should_raise_value_error__when_label_is_invalid() -> None:
    with pytest.raises(ValueError) as error:
        AnnotationProposal(
            proposal_id="p-001",
            label="heading",
            page=18,
            bbox=[72.0, 240.0, 520.0, 610.0],
            confidence=0.88,
            metadata={"source": "code"},
        ).validate()
    assert str(error.value) == "AnnotationProposal.label must be one of table, callout, skip"


def test_annotation_proposal__should_raise_value_error__when_bbox_is_malformed() -> None:
    with pytest.raises(ValueError) as error:
        AnnotationProposal.from_dict(
            {
                "proposal_id": "p-001",
                "label": "table",
                "page": 18,
                "bbox": [72.0, 240.0, 520.0],
                "confidence": 0.88,
                "metadata": {"source": "code"},
            }
        )
    assert str(error.value) == "AnnotationProposal.bbox must contain exactly four numeric values"


def test_annotation_proposal__should_raise_value_error__when_page_is_less_than_one() -> None:
    with pytest.raises(ValueError) as error:
        AnnotationProposal.from_dict(
            {
                "proposal_id": "p-001",
                "label": "skip",
                "page": 0,
                "bbox": [72.0, 240.0, 520.0, 610.0],
                "confidence": 0.88,
                "metadata": {"source": "code"},
            }
        )
    assert str(error.value) == "AnnotationProposal.page must be an integer >= 1"


def test_annotation_proposal__should_raise_value_error__when_confidence_is_out_of_range() -> None:
    with pytest.raises(ValueError) as error:
        AnnotationProposal.from_dict(
            {
                "proposal_id": "p-001",
                "label": "skip",
                "page": 1,
                "bbox": [72.0, 240.0, 520.0, 610.0],
                "confidence": 1.5,
                "metadata": {"source": "code"},
            }
        )
    assert str(error.value) == "AnnotationProposal.confidence must be a number between 0.0 and 1.0"


def test_annotation_proposal__should_raise_value_error__when_metadata_source_is_missing() -> None:
    with pytest.raises(ValueError) as error:
        AnnotationProposal.from_dict(
            {
                "proposal_id": "p-001",
                "label": "skip",
                "page": 1,
                "bbox": [72.0, 240.0, 520.0, 610.0],
                "confidence": 0.5,
                "metadata": {"scope": "full-page"},
            }
        )
    assert str(error.value) == "AnnotationProposal.metadata.source must be one of ai, code, hybrid"


def test_annotation_proposal__should_raise_value_error__when_metadata_is_not_json_safe() -> None:
    with pytest.raises(ValueError) as error:
        AnnotationProposal.from_dict(
            {
                "proposal_id": "p-001",
                "label": "skip",
                "page": 1,
                "bbox": [72.0, 240.0, 520.0, 610.0],
                "confidence": 0.5,
                "metadata": {"source": "code", "raw": object()},
            }
        )
    assert str(error.value) == "AnnotationProposal.metadata.raw must be JSON-serializable"


def test_prep_guidance_resolved__should_raise_value_error__when_region_entry_is_missing_bbox() -> None:
    with pytest.raises(ValueError) as error:
        PrepGuidanceResolved.from_dict(
            {
                "skip_pages": [],
                "skip_regions": [{"page": 18}],
                "table_regions": [],
                "callout_regions": [],
            }
        )
    assert (
        str(error.value)
        == "PrepGuidanceResolved.skip_regions entries must contain page and bbox"
    )


def test_prep_guidance_resolved__should_raise_value_error__when_callout_region_is_missing_label() -> None:
    with pytest.raises(ValueError) as error:
        PrepGuidanceResolved.from_dict(
            {
                "skip_pages": [],
                "skip_regions": [],
                "table_regions": [],
                "callout_regions": [
                    {
                        "page": 18,
                        "bbox": [10.0, 10.0, 20.0, 20.0],
                        "proposal_id": "ap-001",
                    }
                ],
            }
        )
    assert (
        str(error.value)
        == "PrepGuidanceResolved.callout_regions entries must contain page, bbox, and label"
    )


def test_prep_guidance_resolved__should_raise_value_error__when_region_entry_is_missing_page() -> None:
    with pytest.raises(ValueError) as error:
        PrepGuidanceResolved.from_dict(
            {
                "skip_pages": [],
                "skip_regions": [{"bbox": [10.0, 10.0, 20.0, 20.0]}],
                "table_regions": [],
                "callout_regions": [],
            }
        )
    assert (
        str(error.value)
        == "PrepGuidanceResolved.skip_regions entries must contain page and bbox"
    )


def test_prep_guidance_resolved__should_raise_value_error__when_region_extra_value_is_not_json_safe() -> None:
    with pytest.raises(ValueError) as error:
        PrepGuidanceResolved.from_dict(
            {
                "skip_pages": [],
                "skip_regions": [{"page": 18, "bbox": [10.0, 10.0, 20.0, 20.0], "note": object()}],
                "table_regions": [],
                "callout_regions": [],
            }
        )
    assert (
        str(error.value)
        == "PrepGuidanceResolved.skip_regions.note must be JSON-serializable"
    )
