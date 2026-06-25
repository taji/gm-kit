from pathlib import Path

from gm_kit.pdf_convert.prep.contracts import (
    PREP_CONTRACT_VERSION,
    PrepArtifactEntry,
    PrepCommandMetadata,
    PrepManifest,
    build_prep_paths,
)


def test_build_prep_paths__should_return_expected_subtree__when_workspace_provided(
    tmp_path: Path,
) -> None:
    paths = build_prep_paths(tmp_path / "workspace")

    assert paths.root == tmp_path / "workspace" / "prep"
    assert paths.manifest == tmp_path / "workspace" / "prep" / "prep-manifest.json"
    assert paths.state == tmp_path / "workspace" / "prep" / "prep-state.json"
    assert paths.complete == tmp_path / "workspace" / "prep" / "prep-complete.json"
    assert paths.log == tmp_path / "workspace" / "prep" / "logs" / "prep.log"


def test_build_artifacts__should_include_analysis_inventory__when_analysis_paths_provided(
    tmp_path: Path,
) -> None:
    from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths
    from gm_kit.pdf_convert.prep.orchestrator import _build_artifacts

    workspace_dir = tmp_path / "workspace"
    prep_paths = build_prep_paths(workspace_dir)
    analysis_paths = build_analysis_artifact_paths(workspace_dir, pdf_stem="sample")

    for artifact_path in [
        analysis_paths.metadata,
        analysis_paths.preflight_report,
        analysis_paths.image_manifest,
        analysis_paths.no_images_pdf,
        analysis_paths.toc,
        analysis_paths.chapter_index,
        analysis_paths.chunk_plan,
        analysis_paths.guidance_input,
        analysis_paths.annotation_proposals,
        analysis_paths.annotation_review_edits,
        analysis_paths.guidance_resolved,
        analysis_paths.reviewed_guidance,
        analysis_paths.annotated_pdf,
    ]:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("{}", encoding="utf-8")

    artifacts = _build_artifacts(prep_paths, analysis_paths)

    assert artifacts == [
        PrepArtifactEntry(name="prep-manifest.json", status="ready"),
        PrepArtifactEntry(name="prep-state.json", status="ready"),
        PrepArtifactEntry(name="prep-complete.json", status="ready"),
        PrepArtifactEntry(name="logs/prep.log", status="ready"),
        PrepArtifactEntry(name="metadata.json", status="ready"),
        PrepArtifactEntry(name="preflight-report.json", status="ready"),
        PrepArtifactEntry(name="images/image-manifest.json", status="ready"),
        PrepArtifactEntry(name="preprocessed/sample-no-images.pdf", status="ready"),
        PrepArtifactEntry(name="toc-extracted.txt", status="ready"),
        PrepArtifactEntry(name="chapter-index.json", status="ready"),
        PrepArtifactEntry(name="chunk-plan.json", status="ready"),
        PrepArtifactEntry(name="prep-guidance.input.json", status="ready"),
        PrepArtifactEntry(name="annotation-proposals.json", status="ready"),
        PrepArtifactEntry(name="annotation-review.edits.json", status="ready"),
        PrepArtifactEntry(name="prep-guidance.resolved.json", status="ready"),
        PrepArtifactEntry(name="prep-guidance.reviewed.json", status="ready"),
        PrepArtifactEntry(name="annotated-prep.pdf", status="ready"),
    ]


def test_prep_manifest__should_include_contract_version__when_serialized(
    tmp_path: Path,
) -> None:
    manifest = PrepManifest(
        contract_version=PREP_CONTRACT_VERSION,
        pdf_path=str(tmp_path / "sample.pdf"),
        workspace_path=str(tmp_path / "workspace"),
        command_metadata=PrepCommandMetadata(
            command_name="analyze-and-prep-pdf",
            resume_requested=True,
        ),
        artifacts=[PrepArtifactEntry(name="prep-state.json", status="ready")],
        phase_keys=["prep.initialize-workspace"],
        step_keys=["prep.initialize-workspace.bootstrap"],
        completed=False,
    )

    payload = manifest.to_dict()

    assert payload["contract_version"] == PREP_CONTRACT_VERSION
    assert payload["command_metadata"] == {
        "command_name": "analyze-and-prep-pdf",
        "resume_requested": True,
    }
    assert payload["artifacts"] == [{"name": "prep-state.json", "status": "ready"}]
    assert payload["failure_phase_key"] is None
    assert payload["failure_step_key"] is None
    assert payload["failure_message"] is None


def test_prep_manifest__should_reconstruct_from_dict__when_payload_is_valid(
    tmp_path: Path,
) -> None:
    payload = {
        "contract_version": PREP_CONTRACT_VERSION,
        "pdf_path": str(tmp_path / "sample.pdf"),
        "workspace_path": str(tmp_path / "workspace"),
        "command_metadata": {
            "command_name": "analyze-and-prep-pdf",
            "resume_requested": True,
        },
        "artifacts": [{"name": "prep-state.json", "status": "ready"}],
        "phase_keys": ["prep.initialize-workspace"],
        "step_keys": ["prep.initialize-workspace.bootstrap"],
        "completed": False,
    }

    manifest = PrepManifest.from_dict(payload)

    assert manifest.command_metadata.command_name == "analyze-and-prep-pdf"
    assert manifest.command_metadata.resume_requested is True
    assert manifest.artifacts == [PrepArtifactEntry(name="prep-state.json", status="ready")]
    assert manifest.failure_phase_key is None
    assert manifest.failure_step_key is None
    assert manifest.failure_message is None


def test_prep_manifest__should_roundtrip_failure_fields__when_failure_metadata_present(
    tmp_path: Path,
) -> None:
    payload = {
        "contract_version": PREP_CONTRACT_VERSION,
        "pdf_path": str(tmp_path / "sample.pdf"),
        "workspace_path": str(tmp_path / "workspace"),
        "command_metadata": {
            "command_name": "analyze-and-prep-pdf",
            "resume_requested": False,
        },
        "artifacts": [{"name": "prep-state.json", "status": "ready"}],
        "phase_keys": ["prep.initialize-workspace"],
        "step_keys": ["prep.initialize-workspace.bootstrap"],
        "completed": False,
        "failure_phase_key": "prep.extract-assets",
        "failure_step_key": "prep.extract-assets.extract-images",
        "failure_message": "prep.extract-assets.extract-images failed",
    }

    manifest = PrepManifest.from_dict(payload)

    assert manifest.failure_phase_key == "prep.extract-assets"
    assert manifest.failure_step_key == "prep.extract-assets.extract-images"
    assert manifest.failure_message == "prep.extract-assets.extract-images failed"


def test_prep_manifest__should_reject_malformed_payload__when_command_metadata_is_missing() -> None:
    payload = {
        "contract_version": PREP_CONTRACT_VERSION,
        "pdf_path": "/tmp/sample.pdf",
        "workspace_path": "/tmp/workspace",
        "artifacts": [],
        "phase_keys": [],
        "step_keys": [],
        "completed": False,
    }

    try:
        PrepManifest.from_dict(payload)
    except ValueError as error:
        assert "command_metadata" in str(error)
    else:  # pragma: no cover - safety guard for test intent
        raise AssertionError("PrepManifest.from_dict() should reject malformed payloads")


def test_prep_manifest__should_reject_malformed_payload__when_artifacts_are_not_list() -> None:
    payload = {
        "contract_version": PREP_CONTRACT_VERSION,
        "pdf_path": "/tmp/sample.pdf",
        "workspace_path": "/tmp/workspace",
        "command_metadata": {
            "command_name": "analyze-and-prep-pdf",
            "resume_requested": False,
        },
        "artifacts": "prep-state.json",
        "phase_keys": [],
        "step_keys": [],
        "completed": False,
    }

    try:
        PrepManifest.from_dict(payload)
    except ValueError as error:
        assert "artifacts" in str(error)
    else:  # pragma: no cover - safety guard for test intent
        raise AssertionError("PrepManifest.from_dict() should reject malformed payloads")
