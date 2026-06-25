import pytest

from gm_kit.pdf_convert.prep.contracts import (
    AnnotationReviewEdits,
    PrepGuidanceInput,
)


def test_annotation_review_edits__should_roundtrip_review_state__when_payload_is_valid() -> None:
    edits = AnnotationReviewEdits(
        review_mode="interactive",
        review_status="revised",
        skip_ranges_input="2,5,12-14",
        skip_pages_explicit=[2, 5, 12, 13, 14],
        proposal_decisions={"ap-001": "accept", "ap-002": "reject"},
        updated_regions={
            "ap-003": {
                "page": 18,
                "bbox": [72.0, 250.0, 520.0, 600.0],
                "label": "table",
            }
        },
        notes="",
    )

    payload = edits.to_dict()
    restored = AnnotationReviewEdits.from_dict(payload)

    assert restored == edits


def test_prep_guidance_input__should_roundtrip_review_flags__when_review_fields_are_present() -> None:
    guidance = PrepGuidanceInput(
        prefer_detect_tables=True,
        prefer_detect_callouts=True,
        prefer_skip_full_page_artifacts=True,
        review_requested=True,
        auto_accept_annotations=False,
        capture_skip_intent=True,
    )

    payload = guidance.to_dict()
    restored = PrepGuidanceInput.from_dict(payload)

    assert restored == guidance


def test_annotation_review_edits__should_raise_value_error__when_review_mode_is_invalid() -> None:
    payload: dict[str, object] = {
        "review_mode": "manualish",
        "review_status": "pending",
        "skip_ranges_input": "",
        "skip_pages_explicit": [],
        "proposal_decisions": {},
        "updated_regions": {},
        "notes": "",
    }

    with pytest.raises(ValueError) as error:
        AnnotationReviewEdits.from_dict(payload)

    assert (
        str(error.value)
        == "AnnotationReviewEdits.review_mode must be one of auto_accept, bypass, interactive"
    )


def test_annotation_review_edits__should_raise_value_error__when_review_status_is_invalid() -> None:
    payload: dict[str, object] = {
        "review_mode": "interactive",
        "review_status": "partially_accepted",
        "skip_ranges_input": "",
        "skip_pages_explicit": [],
        "proposal_decisions": {},
        "updated_regions": {},
        "notes": "",
    }

    with pytest.raises(ValueError) as error:
        AnnotationReviewEdits.from_dict(payload)

    assert (
        str(error.value)
        == "AnnotationReviewEdits.review_status must be one of accepted, auto_accepted, pending, revised"
    )


def test_annotation_review_edits__should_raise_value_error__when_proposal_decision_is_invalid() -> None:
    payload: dict[str, object] = {
        "review_mode": "interactive",
        "review_status": "revised",
        "skip_ranges_input": "",
        "skip_pages_explicit": [],
        "proposal_decisions": {"ap-001": "keep"},
        "updated_regions": {},
        "notes": "",
    }

    with pytest.raises(ValueError) as error:
        AnnotationReviewEdits.from_dict(payload)

    assert (
        str(error.value)
        == "AnnotationReviewEdits.proposal_decisions.ap-001 must be one of accept, edit, reject"
    )


def test_annotation_review_edits__should_raise_value_error__when_updated_region_label_is_invalid() -> None:
    payload: dict[str, object] = {
        "review_mode": "interactive",
        "review_status": "revised",
        "skip_ranges_input": "",
        "skip_pages_explicit": [],
        "proposal_decisions": {},
        "updated_regions": {
            "ap-003": {
                "page": 18,
                "bbox": [72.0, 250.0, 520.0, 600.0],
                "label": "header",
            }
        },
        "notes": "",
    }

    with pytest.raises(ValueError) as error:
        AnnotationReviewEdits.from_dict(payload)

    assert (
        str(error.value)
        == "AnnotationReviewEdits.updated_regions.ap-003.label must be one of callout, skip, table"
    )


def test_annotation_review_edits__should_raise_value_error__when_updated_region_is_missing_required_field() -> None:
    payload: dict[str, object] = {
        "review_mode": "interactive",
        "review_status": "revised",
        "skip_ranges_input": "",
        "skip_pages_explicit": [],
        "proposal_decisions": {},
        "updated_regions": {
            "ap-003": {
                "page": 18,
                "bbox": [72.0, 250.0, 520.0, 600.0],
            }
        },
        "notes": "",
    }

    with pytest.raises(ValueError) as error:
        AnnotationReviewEdits.from_dict(payload)

    assert (
        str(error.value)
        == "AnnotationReviewEdits.updated_regions.ap-003 must contain page, bbox, and label"
    )


def test_annotation_review_edits__should_raise_value_error__when_skip_pages_explicit_contains_zero() -> None:
    payload: dict[str, object] = {
        "review_mode": "bypass",
        "review_status": "accepted",
        "skip_ranges_input": "0",
        "skip_pages_explicit": [0],
        "proposal_decisions": {},
        "updated_regions": {},
        "notes": "",
    }

    with pytest.raises(ValueError) as error:
        AnnotationReviewEdits.from_dict(payload)

    assert (
        str(error.value)
        == "AnnotationReviewEdits.skip_pages_explicit entries must be integers >= 1"
    )
