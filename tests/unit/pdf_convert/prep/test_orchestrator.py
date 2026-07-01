from __future__ import annotations

import inspect
import json
from pathlib import Path

import fitz  # type: ignore[import-untyped]

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep import (
    PREP_PHASE_KEYS,
    AnnotationProposal,
    AnnotationReviewEdits,
    PrepGuidanceInput,
    PrepGuidanceResolved,
    PrepOrchestrator,
    PrepRegistry,
    build_annotation_proposals,
    build_annotation_review_edits,
    build_final_resolved_guidance,
    build_resolved_guidance,
)
from gm_kit.pdf_convert.prep.analysis_artifacts import PrepAnalysisArtifactPaths
from gm_kit.pdf_convert.prep.registry_types import PrepPhaseDefinition
from gm_kit.pdf_convert.prep.state import PrepRunState, PrepStatus, load_prep_state


def _write_sample_pdf(path: Path, *, page_count: int = 1, toc: list[list[object]] | None = None) -> None:
    document = fitz.open()
    for page_index in range(page_count):
        page = document.new_page()
        page.insert_text((72, 72), f"Prep sample {page_index + 1}")
    if toc is None:
        toc = [[1, "Introduction", 1], [2, "Details", 1]]
    document.set_toc(toc)
    document.save(path)
    document.close()


def test_run_new_prep__should_finalize_manifest_after_completion_artifacts__when_workspace_is_new(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from gm_kit.pdf_convert.prep import orchestrator as orchestrator_module

    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(pdf_path)
    workspace_path = tmp_path / "workspace"
    write_events: list[tuple[str, object]] = []
    original_write_json = orchestrator_module._write_json
    original_save_prep_state = orchestrator_module.save_prep_state

    def capture_write_json(path: Path, payload: dict[str, object]) -> None:
        if path.name == "prep-manifest.json":
            write_events.append((path.name, payload["completed"]))
        elif path.name == "prep-complete.json":
            write_events.append((path.name, payload["status"]))
        original_write_json(path, payload)

    def capture_save_prep_state(path: Path, state: PrepRunState) -> None:
        write_events.append((path.name, state.status.value))
        original_save_prep_state(path, state)

    monkeypatch.setattr(orchestrator_module, "_write_json", capture_write_json)
    monkeypatch.setattr(orchestrator_module, "save_prep_state", capture_save_prep_state)

    exit_code = PrepOrchestrator().run_new_prep(
        pdf_path=pdf_path,
        output_dir=workspace_path,
    )

    prep_root = workspace_path / "prep"
    manifest_payload = json.loads((prep_root / "prep-manifest.json").read_text(encoding="utf-8"))
    complete_payload = json.loads((prep_root / "prep-complete.json").read_text(encoding="utf-8"))

    assert exit_code == ExitCode.SUCCESS
    assert write_events[0] == ("prep-state.json", PrepStatus.RUNNING.value)
    assert write_events[1] == ("prep-manifest.json", False)
    assert write_events[-3:] == [
        ("prep-state.json", PrepStatus.COMPLETED.value),
        ("prep-complete.json", PrepStatus.COMPLETED.value),
        ("prep-manifest.json", True),
    ]
    assert len(write_events) == 14
    assert manifest_payload["workspace_path"] == str(workspace_path.resolve())
    assert manifest_payload["phase_keys"] == list(PREP_PHASE_KEYS)
    assert manifest_payload["step_keys"] == [
        "prep.analyze-document.extract-metadata",
        "prep.extract-assets.extract-images",
        "prep.extract-assets.create-no-images-pdf",
        "prep.derive-structure.acquire-canonical-toc",
        "prep.plan-chunks.build-chunk-plan",
        "prep.prepare-guidance.write-guidance-defaults",
        "prep.propose-annotations.generate-annotation-proposals",
        "prep.review-annotations.seed-review-artifacts",
        "prep.review-annotations.render-annotated-pdf",
    ]
    assert manifest_payload["completed"] is True
    assert manifest_payload["failure_phase_key"] is None
    assert manifest_payload["failure_step_key"] is None
    assert manifest_payload["failure_message"] is None
    assert manifest_payload["artifacts"] == [
        {"name": "prep-manifest.json", "status": "ready"},
        {"name": "prep-state.json", "status": "ready"},
        {"name": "prep-complete.json", "status": "ready"},
        {"name": "logs/prep.log", "status": "ready"},
        {"name": "metadata.json", "status": "ready"},
        {"name": "preflight-report.json", "status": "ready"},
        {"name": "images/image-manifest.json", "status": "ready"},
        {"name": "preprocessed/sample-no-images.pdf", "status": "ready"},
        {"name": "toc-extracted.txt", "status": "ready"},
        {"name": "prep-guidance.defaults.json", "status": "ready"},
        {"name": "annotation-proposals.json", "status": "ready"},
        {"name": "annotation-review.edits.json", "status": "ready"},
        {"name": "prep-guidance.resolved.json", "status": "ready"},
        {"name": "annotated-prep.pdf", "status": "ready"},
    ]
    assert complete_payload["status"] == PrepStatus.COMPLETED.value
    assert complete_payload["manifest_path"] == str(prep_root / "prep-manifest.json")
    assert (prep_root / "metadata.json").exists()
    assert (prep_root / "preflight-report.json").exists()
    assert (prep_root / "images" / "image-manifest.json").exists()
    assert (prep_root / "preprocessed" / "sample-no-images.pdf").exists()
    assert (prep_root / "toc-extracted.txt").exists()
    assert (prep_root / "prep-guidance.defaults.json").exists()
    assert (prep_root / "annotation-proposals.json").exists()
    assert (prep_root / "prep-guidance.resolved.json").exists()

    state = load_prep_state(prep_root / "prep-state.json")
    assert state is not None
    assert state.status == PrepStatus.COMPLETED
    assert state.current_phase_key is None
    assert state.completed_steps == manifest_payload["step_keys"]
    log_output = (prep_root / "logs" / "prep.log").read_text(encoding="utf-8")
    assert "Phase 100: Initialize Workspace (prep.initialize-workspace) started" in log_output
    assert "Phase 200: Analyze Document (prep.analyze-document) started" in log_output
    assert "Phase 500: Plan Chunks (prep.plan-chunks) started" in log_output
    assert "Phase 600: Prepare Guidance (prep.prepare-guidance) started" in log_output
    assert "Phase 700: Propose Annotations (prep.propose-annotations) started" in log_output
    assert "Phase 800: Review Annotations (prep.review-annotations) started" in log_output
    assert (
        "Step 200.100: Extract Metadata And Preflight (prep.analyze-document.extract-metadata) started"
        in log_output
    )
    assert (
        "Step 400.100: Acquire Canonical TOC (prep.derive-structure.acquire-canonical-toc) completed"
        in log_output
    )
    assert "Step 500.100: Build Chunk Plan (prep.plan-chunks.build-chunk-plan) completed" in log_output
    assert (
        "Step 600.100: Write Guidance Defaults (prep.prepare-guidance.write-guidance-defaults) completed"
        in log_output
    )
    assert (
        "Step 700.100: Generate Annotation Proposals "
        "(prep.propose-annotations.generate-annotation-proposals) completed"
        in log_output
    )
    assert (
        "Step 800.100: Seed Annotation Review "
        "(prep.review-annotations.seed-review-artifacts) completed"
        in log_output
    )
    assert (
        "Step 800.200: Render Annotated Prep PDF "
        "(prep.review-annotations.render-annotated-pdf) completed"
        in log_output
    )

    guidance_defaults_payload = json.loads(
        (prep_root / "prep-guidance.defaults.json").read_text(encoding="utf-8")
    )
    annotation_proposals_payload = json.loads(
        (prep_root / "annotation-proposals.json").read_text(encoding="utf-8")
    )
    guidance_resolved_payload = json.loads(
        (prep_root / "prep-guidance.resolved.json").read_text(encoding="utf-8")
    )

    assert guidance_defaults_payload == PrepGuidanceInput().to_dict()
    assert isinstance(annotation_proposals_payload, list)
    assert annotation_proposals_payload == []
    assert guidance_resolved_payload == PrepGuidanceResolved(
        skip_pages=[],
        skip_regions=[],
        table_regions=[],
        callout_regions=[],
    ).to_dict()
    assert not (prep_root / "prep-guidance.reviewed.json").exists()


def test_run_new_prep__should_emit_chunk_planning_artifacts__when_document_exceeds_budget(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(
        pdf_path,
        page_count=12,
        toc=[
            [1, "Contents", 1],
            [1, "Chapter 1: Barovia", 2],
            [1, "Chapter 2: The Village", 6],
            [1, "Appendix A: Resources", 11],
        ],
    )
    workspace_path = tmp_path / "workspace"

    exit_code = PrepOrchestrator().run_new_prep(
        pdf_path=pdf_path,
        output_dir=workspace_path,
    )

    prep_root = workspace_path / "prep"
    manifest_payload = json.loads((prep_root / "prep-manifest.json").read_text(encoding="utf-8"))
    chapter_index_payload = json.loads((prep_root / "chapter-index.json").read_text(encoding="utf-8"))
    chunk_plan_payload = json.loads((prep_root / "chunk-plan.json").read_text(encoding="utf-8"))
    log_output = (prep_root / "logs" / "prep.log").read_text(encoding="utf-8")

    assert exit_code == ExitCode.SUCCESS
    assert chapter_index_payload["document_page_count"] == 12
    assert [section["section_id"] for section in chapter_index_payload["sections"]] == [
        "001-front_matter-contents",
        "002-body-chapter-1-barovia",
        "003-body-chapter-2-the-village",
        "004-appendix-appendix-a-resources",
    ]
    assert [chunk["chunk_kind"] for chunk in chunk_plan_payload["chunks"]] == [
        "chapter",
        "chapter",
        "chapter",
        "chapter",
    ]
    assert manifest_payload["artifacts"][-4:] == [
        {"name": "annotation-proposals.json", "status": "ready"},
        {"name": "annotation-review.edits.json", "status": "ready"},
        {"name": "prep-guidance.resolved.json", "status": "ready"},
        {"name": "annotated-prep.pdf", "status": "ready"},
    ]
    assert manifest_payload["artifacts"][-7:-4] == [
        {"name": "chapter-index.json", "status": "ready"},
        {"name": "chunk-plan.json", "status": "ready"},
        {"name": "prep-guidance.defaults.json", "status": "ready"},
    ]
    assert "Phase 500: Plan Chunks (prep.plan-chunks) started" in log_output
    assert (
        "Step 500.100: Build Chunk Plan (prep.plan-chunks.build-chunk-plan) completed"
        in log_output
    )
    assert (
        "Step 700.100: Generate Annotation Proposals "
        "(prep.propose-annotations.generate-annotation-proposals) completed"
        in log_output
    )
    assert "Phase 800: Review Annotations (prep.review-annotations) started" in log_output
    assert (
        "Step 800.100: Seed Annotation Review "
        "(prep.review-annotations.seed-review-artifacts) completed"
        in log_output
    )
    assert (
        "Step 800.200: Render Annotated Prep PDF "
        "(prep.review-annotations.render-annotated-pdf) completed"
        in log_output
    )

    annotation_proposals_payload = json.loads(
        (prep_root / "annotation-proposals.json").read_text(encoding="utf-8")
    )
    guidance_resolved_payload = json.loads(
        (prep_root / "prep-guidance.resolved.json").read_text(encoding="utf-8")
    )

    expected_proposals = [
        proposal.to_dict()
        for proposal in build_annotation_proposals(
            page_count=12,
            images_total_count=0,
            chunk_plan=chunk_plan_payload,
        )
    ]
    expected_resolved = build_resolved_guidance(
        [AnnotationProposal.from_dict(proposal) for proposal in annotation_proposals_payload]
    ).to_dict()

    assert annotation_proposals_payload == expected_proposals
    assert guidance_resolved_payload == expected_resolved


def test_run_new_prep__should_accept_auto_proceed_flag__when_called_for_cli_compatibility(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(pdf_path, page_count=3)

    signature = inspect.signature(PrepOrchestrator.run_new_prep)
    auto_proceed_parameter = signature.parameters["auto_proceed"]
    exit_code = PrepOrchestrator().run_new_prep(
        pdf_path=pdf_path,
        output_dir=tmp_path / "workspace",
        auto_proceed=True,
    )

    assert auto_proceed_parameter.default is False
    assert exit_code == ExitCode.SUCCESS


def test_show_status__should_return_success__when_completed_prep_artifacts_exist(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(pdf_path)
    workspace_path = tmp_path / "workspace"
    orchestrator = PrepOrchestrator()

    setup_exit_code = orchestrator.run_new_prep(
        pdf_path=pdf_path,
        output_dir=workspace_path,
    )
    exit_code = orchestrator.show_status(workspace=workspace_path)

    assert setup_exit_code == ExitCode.SUCCESS
    assert exit_code == ExitCode.SUCCESS


def test_resume_prep__should_return_success__when_prep_is_already_completed(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(pdf_path)
    workspace_path = tmp_path / "workspace"
    orchestrator = PrepOrchestrator()

    setup_exit_code = orchestrator.run_new_prep(
        pdf_path=pdf_path,
        output_dir=workspace_path,
    )
    exit_code = orchestrator.resume_prep(
        workspace=workspace_path,
        auto_proceed=True,
    )

    assert setup_exit_code == ExitCode.SUCCESS
    assert exit_code == ExitCode.SUCCESS


def test_revise_prep_guidance__should_write_reviewed_guidance__when_review_artifacts_exist(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(pdf_path, page_count=3)
    workspace_path = tmp_path / "workspace"
    orchestrator = PrepOrchestrator()

    setup_exit_code = orchestrator.run_new_prep(
        pdf_path=pdf_path,
        output_dir=workspace_path,
    )

    prep_root = workspace_path / "prep"
    review_edits_payload = {
        "review_mode": "interactive",
        "review_status": "revised",
        "skip_ranges_input": "2",
        "skip_pages_explicit": [2],
        "proposal_decisions": {},
        "updated_regions": {},
        "notes": "",
    }
    (prep_root / "annotation-review.edits.json").write_text(
        json.dumps(review_edits_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    revise_exit_code = orchestrator.revise_prep_guidance(workspace_path)

    reviewed_payload = json.loads(
        (prep_root / "prep-guidance.reviewed.json").read_text(encoding="utf-8")
    )
    manifest_payload = json.loads((prep_root / "prep-manifest.json").read_text(encoding="utf-8"))

    assert setup_exit_code == ExitCode.SUCCESS
    assert revise_exit_code == ExitCode.SUCCESS
    assert reviewed_payload["skip_pages"] == [2]
    assert any(
        artifact["name"] == "prep-guidance.reviewed.json"
        for artifact in manifest_payload["artifacts"]
    )


def test_revise_prep_guidance__should_finalize_callout_reviews_into_shared_prep_guidance__when_callout_proposals_exist(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from gm_kit.pdf_convert.prep import handlers as prep_handlers

    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(pdf_path, page_count=3)
    workspace_path = tmp_path / "workspace"

    def fake_extract_images(
        *,
        analysis_paths: PrepAnalysisArtifactPaths,
        **_context: object,
    ) -> None:
        analysis_paths.images_dir.mkdir(parents=True, exist_ok=True)
        analysis_paths.image_manifest.write_text(
            json.dumps(
                {
                    "images": [],
                    "total_count": 2,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(prep_handlers, "handle_extract_images", fake_extract_images)
    orchestrator = PrepOrchestrator()

    setup_exit_code = orchestrator.run_new_prep(
        pdf_path=pdf_path,
        output_dir=workspace_path,
    )

    prep_root = workspace_path / "prep"
    annotation_proposals_payload = json.loads(
        (prep_root / "annotation-proposals.json").read_text(encoding="utf-8")
    )
    callout_proposals = [
        proposal for proposal in annotation_proposals_payload if proposal["label"] == "callout"
    ]
    review_edits_payload = {
        "review_mode": "interactive",
        "review_status": "revised",
        "skip_ranges_input": "",
        "skip_pages_explicit": [],
        "proposal_decisions": {
            callout_proposals[0]["proposal_id"]: "accept",
            callout_proposals[1]["proposal_id"]: "reject",
        },
        "updated_regions": {},
        "notes": "",
    }
    accepted_callout_proposal = next(
        proposal
        for proposal in callout_proposals
        if proposal["proposal_id"] in review_edits_payload["proposal_decisions"]
        and review_edits_payload["proposal_decisions"][proposal["proposal_id"]] == "accept"
    )
    (prep_root / "annotation-review.edits.json").write_text(
        json.dumps(review_edits_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    revise_exit_code = orchestrator.revise_prep_guidance(workspace_path)

    reviewed_payload = json.loads(
        (prep_root / "prep-guidance.reviewed.json").read_text(encoding="utf-8")
    )
    manifest_payload = json.loads((prep_root / "prep-manifest.json").read_text(encoding="utf-8"))

    assert setup_exit_code == ExitCode.SUCCESS
    assert (prep_root / "annotated-prep.pdf").exists()
    assert revise_exit_code == ExitCode.SUCCESS
    assert reviewed_payload["callout_regions"] == [
        {
            "page": accepted_callout_proposal["page"],
            "bbox": accepted_callout_proposal["bbox"],
            "proposal_id": accepted_callout_proposal["proposal_id"],
            "label": "callout_gm",
        }
    ]
    assert reviewed_payload["table_regions"] == []
    assert any(
        artifact["name"] == "annotation-proposals.json"
        for artifact in manifest_payload["artifacts"]
    )
    assert any(
        artifact["name"] == "annotated-prep.pdf" for artifact in manifest_payload["artifacts"]
    )
    assert any(
        artifact["name"] == "prep-guidance.reviewed.json"
        for artifact in manifest_payload["artifacts"]
    )
    assert not (prep_root / "callout-manifest.json").exists()


def test_run_new_prep__should_return_file_error_without_contract_files__when_pdf_missing(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "missing.pdf"
    workspace_path = tmp_path / "workspace"

    exit_code = PrepOrchestrator().run_new_prep(pdf_path=pdf_path, output_dir=workspace_path)

    assert exit_code == ExitCode.FILE_ERROR
    assert not (workspace_path / "prep" / "prep-manifest.json").exists()
    assert not (workspace_path / "prep" / "prep-state.json").exists()
    assert not (workspace_path / "prep" / "prep-complete.json").exists()
    assert not (workspace_path / "prep" / "logs" / "prep.log").exists()


def test_run_new_prep__should_record_failure_details_in_manifest__when_step_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from gm_kit.pdf_convert.prep import handlers as prep_handlers

    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(pdf_path)
    workspace_path = tmp_path / "workspace"

    def broken_extract_metadata_and_preflight(**_context: object) -> None:
        raise ValueError("credential=abc123 /tmp/secret.pdf")

    monkeypatch.setattr(
        prep_handlers,
        "handle_extract_metadata_and_preflight",
        broken_extract_metadata_and_preflight,
    )

    exit_code = PrepOrchestrator().run_new_prep(pdf_path=pdf_path, output_dir=workspace_path)

    prep_root = workspace_path / "prep"
    manifest_payload = json.loads((prep_root / "prep-manifest.json").read_text(encoding="utf-8"))
    log_output = (prep_root / "logs" / "prep.log").read_text(encoding="utf-8")

    assert exit_code == ExitCode.FILE_ERROR
    assert (prep_root / "prep-state.json").exists()
    assert not (prep_root / "prep-complete.json").exists()
    assert manifest_payload["completed"] is False
    assert manifest_payload["failure_phase_key"] == "prep.analyze-document"
    assert manifest_payload["failure_step_key"] == "prep.analyze-document.extract-metadata"
    assert "credential=[REDACTED] [REDACTED_PATH]" in manifest_payload["failure_message"]
    assert "Phase 100: Initialize Workspace (prep.initialize-workspace) started" in log_output
    assert "Phase 200: Analyze Document (prep.analyze-document) started" in log_output
    assert (
        "Step 200.100: Extract Metadata And Preflight (prep.analyze-document.extract-metadata) started"
        in log_output
    )
    assert "ERROR: prep.analyze-document.extract-metadata failed" in log_output


def test_run_new_prep__should_use_first_registry_phase_for_running_state__when_registry_order_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from gm_kit.pdf_convert.prep import orchestrator as orchestrator_module

    pdf_path = tmp_path / "sample.pdf"
    _write_sample_pdf(pdf_path)

    reversed_registry = PrepRegistry(
        phases=[
            PrepPhaseDefinition(
                phase_key=phase_key,
                order=(index + 1) * 100,
                display_name=phase_key,
            )
            for index, phase_key in enumerate(reversed(PREP_PHASE_KEYS))
        ],
        steps=[],
    )
    saved_states: list[PrepRunState] = []
    original_save_prep_state = orchestrator_module.save_prep_state

    def capture_save(path: Path, state: PrepRunState) -> None:
        saved_states.append(state)
        original_save_prep_state(path, state)

    monkeypatch.setattr(orchestrator_module, "save_prep_state", capture_save)

    exit_code = PrepOrchestrator(registry=reversed_registry).run_new_prep(
        pdf_path=pdf_path,
        output_dir=tmp_path / "workspace",
    )

    assert exit_code == ExitCode.SUCCESS
    assert saved_states[0].status == PrepStatus.RUNNING
    assert saved_states[0].current_phase_key == list(reversed(PREP_PHASE_KEYS))[0]


def test_build_default_registry__should_follow_shared_phase_key_export__when_phase_keys_change(
    monkeypatch,
) -> None:
    from gm_kit.pdf_convert.prep import orchestrator as orchestrator_module

    reordered_phase_keys = tuple(reversed(PREP_PHASE_KEYS))
    monkeypatch.setattr(
        orchestrator_module,
        "PREP_PHASE_KEYS",
        reordered_phase_keys,
        raising=False,
    )

    registry = orchestrator_module._build_default_registry()

    assert [phase.phase_key for phase in registry.get_ordered_phases()] == list(
        reordered_phase_keys
    )


def test_run_new_prep__should_export_public_symbols__when_prep_package_imported() -> None:
    from gm_kit.pdf_convert import prep

    assert "AnnotationProposal" in prep.__all__
    assert "AnnotationReviewEdits" in prep.__all__
    assert "PrepOrchestrator" in prep.__all__
    assert "PREP_PHASE_KEYS" in prep.__all__
    assert "PrepGuidanceInput" in prep.__all__
    assert "PrepGuidanceResolved" in prep.__all__
    assert "build_annotation_proposals" in prep.__all__
    assert "build_annotation_review_edits" in prep.__all__
    assert "build_final_resolved_guidance" in prep.__all__
    assert "build_resolved_guidance" in prep.__all__
    assert "handle_finalize_reviewed_guidance" in prep.__all__
    assert "handle_render_annotated_prep_pdf" in prep.__all__
    assert "handle_seed_annotation_review" in prep.__all__
    assert "load_effective_prep_guidance" in prep.__all__
    assert "render_annotated_prep_pdf" in prep.__all__
    assert prep.AnnotationProposal is AnnotationProposal
    assert prep.AnnotationReviewEdits is AnnotationReviewEdits
    assert prep.PrepGuidanceInput is PrepGuidanceInput
    assert prep.PrepGuidanceResolved is PrepGuidanceResolved
    assert prep.PrepOrchestrator is PrepOrchestrator
    assert prep.PREP_PHASE_KEYS == PREP_PHASE_KEYS
    assert prep.build_annotation_proposals is build_annotation_proposals
    assert prep.build_annotation_review_edits is build_annotation_review_edits
    assert prep.build_final_resolved_guidance is build_final_resolved_guidance
    assert prep.build_resolved_guidance is build_resolved_guidance
    assert prep.load_effective_prep_guidance.__name__ == "load_effective_prep_guidance"
