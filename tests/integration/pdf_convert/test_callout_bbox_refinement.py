from __future__ import annotations

import json
import os
from pathlib import Path

import fitz  # type: ignore[import-untyped]

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.callout_detection import detect_callout_proposals
from gm_kit.pdf_convert.prep.contracts import PrepGuidanceInput
from gm_kit.pdf_convert.prep.orchestrator import PrepOrchestrator

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


def test_analyze_and_prep_pdf__should_pause_and_resume_handoff__when_refinement_mode_is_handoff(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "homebrewery-prep"
    prep_root = workspace / "prep"
    request_path = prep_root / "annotation-refinement" / "annotation-refinement-request.json"
    refined_path = prep_root / "annotation-refined-proposals.json"

    previous_mode = os.environ.get("GMKIT_CALL_OUT_REFINEMENT_MODE")
    os.environ["GMKIT_CALL_OUT_REFINEMENT_MODE"] = "handoff"
    try:
        analyze_exit_code = PrepOrchestrator().run_new_prep(
            pdf_path=FIXTURE_PDF,
            output_dir=workspace,
        )
    finally:
        if previous_mode is None:
            os.environ.pop("GMKIT_CALL_OUT_REFINEMENT_MODE", None)
        else:
            os.environ["GMKIT_CALL_OUT_REFINEMENT_MODE"] = previous_mode

    assert analyze_exit_code == ExitCode.SUCCESS
    assert request_path.exists()
    assert not refined_path.exists()

    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    proposals_payload = json.loads((prep_root / "annotation-proposals.json").read_text(encoding="utf-8"))
    refined_path.write_text(
        json.dumps(proposals_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert request_payload["request_status"] == "ready_for_outer_agent"
    assert request_payload["refinement_mode"] == "handoff"

    resume_exit_code = PrepOrchestrator().resume_prep(workspace)
    assert resume_exit_code == ExitCode.SUCCESS
    assert (prep_root / "prep-complete.json").exists()
    assert (prep_root / "annotated-prep.pdf").exists()
