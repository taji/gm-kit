import json
from pathlib import Path

from gm_kit.pdf_convert.prep.analysis_artifacts import build_analysis_artifact_paths
from gm_kit.pdf_convert.prep.resolution import (
    build_effective_prep_artifact_paths,
    validate_required_prep_artifacts,
)


def test_build_effective_prep_artifact_paths__should_choose_reviewed_guidance__when_reviewed_exists(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    prep_root = workspace / "prep"
    prep_root.mkdir(parents=True)
    (prep_root / "prep-guidance.resolved.json").write_text("{}", encoding="utf-8")
    (prep_root / "prep-guidance.reviewed.json").write_text("{}", encoding="utf-8")

    paths = build_effective_prep_artifact_paths(workspace, pdf_stem="sample")

    assert paths.effective_guidance == prep_root / "prep-guidance.reviewed.json"


def test_build_effective_prep_artifact_paths__should_fall_back_to_baseline_guidance__when_reviewed_missing(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    prep_root = workspace / "prep"
    prep_root.mkdir(parents=True)
    (prep_root / "prep-guidance.resolved.json").write_text("{}", encoding="utf-8")

    paths = build_effective_prep_artifact_paths(workspace, pdf_stem="sample")

    assert paths.effective_guidance == prep_root / "prep-guidance.resolved.json"


def test_validate_required_prep_artifacts__should_skip_chunk_plan__when_document_fits_budget(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    paths = build_analysis_artifact_paths(workspace, pdf_stem="sample")
    paths.metadata.parent.mkdir(parents=True, exist_ok=True)
    paths.metadata.write_text(json.dumps({"page_count": 10}), encoding="utf-8")
    paths.preflight_report.write_text("{}", encoding="utf-8")
    paths.toc.write_text("Introduction (page 1)\n", encoding="utf-8")
    paths.guidance_resolved.write_text("{}", encoding="utf-8")

    missing = validate_required_prep_artifacts(paths)

    assert missing == []


def test_validate_required_prep_artifacts__should_require_chunk_artifacts__when_document_exceeds_budget(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    paths = build_analysis_artifact_paths(workspace, pdf_stem="sample")
    paths.metadata.parent.mkdir(parents=True, exist_ok=True)
    paths.metadata.write_text(json.dumps({"page_count": 256}), encoding="utf-8")
    paths.preflight_report.write_text("{}", encoding="utf-8")
    paths.toc.write_text("Introduction (page 1)\n", encoding="utf-8")
    paths.guidance_resolved.write_text("{}", encoding="utf-8")

    missing = validate_required_prep_artifacts(paths)

    assert missing == ["chapter-index.json", "chunk-plan.json"]
