from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from gm_kit.pdf_convert.prep.analysis_artifacts import (
    PrepAnalysisArtifactPaths,
    build_analysis_artifact_paths,
    requires_chunk_plan,
)

REQUIRED_PREP_ARTIFACT_NAMES = (
    "metadata.json",
    "preflight-report.json",
    "toc-extracted.txt",
    "chapter-index.json",
    "chunk-plan.json",
    "prep-guidance.resolved.json",
)


@dataclass(frozen=True)
class EffectivePrepArtifactPaths:
    analysis: PrepAnalysisArtifactPaths
    effective_guidance: Path


def build_effective_prep_artifact_paths(
    workspace_dir: Path,
    pdf_stem: str,
) -> EffectivePrepArtifactPaths:
    analysis = build_analysis_artifact_paths(workspace_dir, pdf_stem=pdf_stem)
    effective_guidance = (
        analysis.reviewed_guidance
        if analysis.reviewed_guidance.exists()
        else analysis.guidance_resolved
    )
    return EffectivePrepArtifactPaths(
        analysis=analysis,
        effective_guidance=effective_guidance,
    )


def validate_required_prep_artifacts(
    analysis_paths: PrepAnalysisArtifactPaths,
) -> list[str]:
    missing_artifacts: list[str] = []
    required_paths = (
        analysis_paths.metadata,
        analysis_paths.preflight_report,
        analysis_paths.toc,
        analysis_paths.guidance_resolved,
    )
    for path in required_paths:
        if not path.exists():
            missing_artifacts.append(path.name)

    if analysis_paths.metadata.exists():
        try:
            metadata_payload = json.loads(analysis_paths.metadata.read_text(encoding="utf-8"))
            page_count = int(metadata_payload["page_count"])
        except Exception:
            missing_artifacts.append(analysis_paths.metadata.name)
            return missing_artifacts
        if requires_chunk_plan(page_count):
            for path in (analysis_paths.chapter_index, analysis_paths.chunk_plan):
                if not path.exists():
                    missing_artifacts.append(path.name)
    return missing_artifacts
